from fastapi import APIRouter, HTTPException
from app.models.schemas import GenerateRequest, GenerateResponse
from app.services.nomgen_core import NomGenService
import time

router  = APIRouter()
service = NomGenService()   # chargé une seule fois au démarrage


@router.post("/generate", response_model=GenerateResponse)
async def generate_names(req: GenerateRequest):
    try:
        t0     = time.time()
        result = service.generate(
            prompt=req.prompt, secteur=req.secteur, langue=req.langue,
            n=req.n, temperature=req.temperature,
            top_k=req.top_k, seed=req.seed,
        )
        return GenerateResponse(
            noms=result["noms"],
            tokens_detectes=result["tokens"],
            duree_ms=round((time.time() - t0) * 1000, 1),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
