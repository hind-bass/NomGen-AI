import re
import time
from fastapi import APIRouter, HTTPException
from app.models.schemas import GenerateRequest, GenerateResponse
from app.services.nomgen_core import NomGenService

router  = APIRouter()
service = NomGenService()   # chargé une seule fois au démarrage


#  NOUVEAUTÉ : FONCTION DE VALIDATION DU PROMPT (Détection de Charabia / Gibberish)
def est_un_prompt_incoherent(prompt: str) -> bool:
    text = prompt.strip()
    
    # 1. Si le prompt est vide ou trop court pour avoir du sens
    if len(text) < 100:
        return True
        
    # 2. Détection de frappes aléatoires continues (ex: "jhdkjhfkdh")
    # Si le texte ne contient aucun espace et dépasse 8 caractères, c'est incohérent
    if " " not in text and len(text) > 8:
        return True
        
    # 3. Vérification de la présence minimale de caractères (lettres FR ou AR)
    has_letters = bool(re.search(r'[a-zA-Z\u0600-\u06FF]', text))
    if not has_letters:
        return True

    return False


@router.post("/generate", response_model=GenerateResponse)
async def generate_names(req: GenerateRequest):
    try:
        t0 = time.time()
        
        # ⚡ SÉCURITÉ : Si le prompt est du charabia, on court-circuite le service NomGenService
        if est_un_prompt_incoherent(req.prompt):
            return GenerateResponse(
                noms=[],
                tokens_detectes=[],
                duree_ms=round((time.time() - t0) * 1000, 1),
            )

        # Logique classique si le prompt est valide
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