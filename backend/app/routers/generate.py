"""
Router de génération — mis à jour Jour 1.
Nouveau : enregistrement de chaque génération dans l'historique DB.
L'auth est optionnelle : les non-connectés peuvent générer mais sans historique.
"""
import re
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.database import get_session
from app.models.schemas import GenerateRequest, GenerateResponse
from app.services.nomgen_core import NomGenService
from app.routers.history import log_generation
from app.services.generation_store_service import save_generated_names

# Import optionnel du user (ne bloque pas si non connecté)
from fastapi import Request
from app.services.auth_service import decode_token

router  = APIRouter()
service = NomGenService()   # Chargé une seule fois au démarrage


def est_un_prompt_incoherent(prompt: str) -> bool:
    """Détecte un prompt vide, trop court, ou rempli de caractères aléatoires."""
    text = prompt.strip()
    if len(text) < 10:
        return True
    if " " not in text and len(text) > 8:
        return True
    has_letters = bool(re.search(r'[a-zA-Z\u0600-\u06FF]', text))
    if not has_letters:
        return True
    return False


def _get_optional_user_id(request: Request) -> Optional[int]:
    """
    Extrait l'user_id depuis le token JWT si présent dans les headers.
    Retourne None si pas de token (utilisateur non connecté).
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    payload = decode_token(token)
    if payload:
        return payload.get("user_id")
    return None


@router.post("/generate", response_model=GenerateResponse)
async def generate_names(
    req: GenerateRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Génère des noms de marque.
    - Si connecté : enregistre la génération dans l'historique.
    - Si non connecté : génère quand même (sans historique).
    """
    try:
        t0 = time.time()

        if est_un_prompt_incoherent(req.prompt):
            return GenerateResponse(
                noms=[],
                tokens_detectes=[],
                duree_ms=round((time.time() - t0) * 1000, 1),
            )

        result = service.generate(
            prompt=req.prompt,
            secteur=req.secteur,
            langue=req.langue,
            n=req.n,
            temperature=req.temperature,
            top_k=req.top_k,
            seed=req.seed,
        )

        # Persistance automatique + IDs pour feedback / fine-tuning
        gen_ids = save_generated_names(
            session=session,
            prompt=req.prompt,
            langue=req.langue,
            categorie=req.secteur,
            type_nom="marque",
            noms=result["noms"],
            mode="A",
        )
        for i, nom_dict in enumerate(result["noms"]):
            if i < len(gen_ids):
                nom_dict["generation_id"] = gen_ids[i]

        # Log dans l'historique si l'utilisateur est connecté
        user_id = _get_optional_user_id(request)
        if user_id:
            log_generation(
                session=session,
                user_id=user_id,
                prompt=req.prompt,
                langue=req.langue,
                secteur=req.secteur,
                n_generated=len(result["noms"]),
                mode="A",
            )

        return GenerateResponse(
            noms=result["noms"],
            tokens_detectes=result["tokens"],
            duree_ms=round((time.time() - t0) * 1000, 1),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
