"""
Router Mode B — Génération via LLM externe (Ollama, Mistral, OpenAI, Allam...).
POST /api/generate-llm
Corps : { prompt, model_key, langue, secteur, type_nom, n, temperature }
"""
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.database import get_session
from app.services.llm_service import llm_router
from app.services.auth_service import decode_token
from app.routers.history import log_generation

router = APIRouter()


# ─── Schémas ─────────────────────────────────────────────────────────────────

class LLMGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=5, description="Description du projet")
    model_key: str = Field(default="ollama-mistral",
                           description="Clé du modèle (voir /api/models/llm-list)")
    langue: str = Field(default="fr", description="'fr' ou 'ar'")
    secteur: str = Field(default="GENERAL")
    type_nom: str = Field(default="marque",
                          description="'marque' ou 'societe'")
    n: int = Field(default=8, ge=1, le=20)
    temperature: float = Field(default=0.9, ge=0.1, le=1.5)


class LLMGeneratedName(BaseModel):
    nom: str
    score: float = 0.0
    langue: str
    secteur: str
    source: str = "llm"          # distingue Mode A (nanogpt) de Mode B (llm)


class LLMGenerateResponse(BaseModel):
    noms: list[LLMGeneratedName]
    model_used: str
    duree_ms: float


# ─── Helper : extraire user_id optionnel depuis le JWT ───────────────────────

def _get_optional_user_id(request: Request) -> Optional[int]:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    payload = decode_token(token)
    if payload:
        return payload.get("user_id")
    return None


# ─── Endpoint principal ───────────────────────────────────────────────────────

@router.post("/generate-llm", response_model=LLMGenerateResponse)
async def generate_names_llm(
    req: LLMGenerateRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Mode B : génère des noms via un LLM externe.
    - Nécessite que le modèle soit disponible (clé API ou Ollama local).
    - Enregistre dans l'historique si l'utilisateur est connecté.
    """
    t0 = time.time()

    # Vérifier que le modèle est disponible avant d'appeler
    is_ok, reason = llm_router.check_model_available(req.model_key)
    if not is_ok:
        raise HTTPException(
            status_code=503,
            detail=f"Modèle '{req.model_key}' non disponible : {reason}. "
                   f"Vérifiez les variables d'environnement ou lancez Ollama."
        )

    try:
        raw_names = await llm_router.generate(
            model_key=req.model_key,
            prompt=req.prompt,
            n=req.n,
            langue=req.langue,
            type_nom=req.type_nom,
            secteur=req.secteur,
            style=req.secteur,
            temperature=req.temperature,
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Erreur lors de l'appel au LLM '{req.model_key}': {str(e)}"
        )

    # Construire la réponse avec score simple
    noms = [
        LLMGeneratedName(
            nom=name,
            score=round(50 + min(len(name) * 3, 40), 1),   # score heuristique basique
            langue=req.langue,
            secteur=req.secteur,
            source="llm",
        )
        for name in raw_names
        if name.strip()
    ]

    # Log historique si connecté
    user_id = _get_optional_user_id(request)
    if user_id:
        log_generation(
            session=session,
            user_id=user_id,
            prompt=req.prompt,
            langue=req.langue,
            secteur=req.secteur,
            n_generated=len(noms),
            mode="B",
        )

    return LLMGenerateResponse(
        noms=noms,
        model_used=req.model_key,
        duree_ms=round((time.time() - t0) * 1000, 1),
    )


# ─── Endpoint utilitaire : lister les modèles disponibles ────────────────────

@router.get("/models/llm-list")
def list_llm_models(langue: Optional[str] = None):
    """
    Retourne la liste des modèles LLM disponibles.
    Filtrage optionnel par langue : ?langue=fr ou ?langue=ar
    """
    models = llm_router.get_available_models(langue=langue)
    return {"models": models, "total": len(models)}