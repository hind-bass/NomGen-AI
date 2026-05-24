import re
import time
from fastapi import APIRouter, HTTPException
from app.models.schemas import GenerateRequest, GenerateResponse
from app.services.nomgen_core import NomGenService

router  = APIRouter()
service = NomGenService()


def est_un_prompt_incoherent(prompt: str) -> bool:
    """
    Retourne True uniquement si le prompt est clairement inutilisable.

    Règles :
      1. Vide ou quasi-vide (< 3 caractères après strip)
      2. Frappe aléatoire continue : aucun espace ET plus de 15 chars
         ex: "jdhfkjhdfkjhdf" → incohérent
      3. Aucune lettre latine ni arabe (uniquement chiffres/symboles)
    """
    text = prompt.strip()

    if len(text) < 3:
        return True

    if " " not in text and len(text) > 15:
        return True

    has_letters = bool(re.search(r'[a-zA-Z\u0600-\u06FF]', text))
    if not has_letters:
        return True

    return False


@router.post("/generate", response_model=GenerateResponse)
async def generate_names(req: GenerateRequest):
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
            generation_type=req.generation_type,
            langue=req.langue,
            n=req.n,
            temperature=req.temperature,
            top_k=req.top_k,
            seed=req.seed,
        )
        return GenerateResponse(
            noms=result["noms"],
            tokens_detectes=result["tokens"],
            duree_ms=round((time.time() - t0) * 1000, 1),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))