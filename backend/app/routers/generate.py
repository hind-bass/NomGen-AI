import re
import time
from fastapi import APIRouter, HTTPException
from app.models.schemas import GenerateRequest, GenerateResponse, CreativityPreset
from app.services.nomgen_core import NomGenService
from app.services.prompt_validation import validate_prompt_coherence
from app.config import CATEGORIES_CONFIG

router = APIRouter()
service = NomGenService()


# Presets de créativité
_CREATIVITY_PRESETS = {
    CreativityPreset.CONSERVATEUR: {"temperature": 0.8, "top_k": 15, "top_p": None},
    CreativityPreset.EQUILIBRE: {"temperature": 1.1, "top_k": 25, "top_p": 0.92},
    CreativityPreset.CREATIF: {"temperature": 1.5, "top_k": 30, "top_p": 0.95},
}


@router.post("/generate", response_model=GenerateResponse)
async def generate_names(req: GenerateRequest):
    try:
        t0 = time.time()

        # Étape 1 : Validation de cohérence
        is_valid, error_msg = validate_prompt_coherence(req.prompt)
        if not is_valid:
            return GenerateResponse(
                noms=[],
                strategy_used="validation_error",
                category_hint=f"validation_error:{error_msg}",
                duree_ms=round((time.time() - t0) * 1000, 1),
            )

        # Étape 2 : Récupérer la configuration de catégorie
        config_type = CATEGORIES_CONFIG['categories'][req.type.value]
        sector_config = next(
            (s for s in config_type['sectors'] if s['id'] == req.category),
            None
        )

        if not sector_config:
            raise HTTPException(400, f"Unknown category: {req.category}")

        # Étape 3 : Appliquer presets de créativité + overrides par catégorie
        preset = req.creativity_preset or CreativityPreset.EQUILIBRE
        preset_config = _CREATIVITY_PRESETS[preset]

        # Overrides explicites si fournis, sinon utiliser category-specific tuning
        temperature = (
            req.temperature
            if req.temperature is not None
            else sector_config.get('tempOverride', preset_config["temperature"])
        )
        top_k = (
            req.top_k
            if req.top_k is not None
            else sector_config.get('topKOverride', preset_config["top_k"])
        )
        top_p = req.top_p if req.top_p is not None else preset_config["top_p"]
        repetition_penalty = req.repetition_penalty or 1.0

        # Augmenter légèrement la température pour l'arabe
        if req.langue == "ar" and req.temperature is None:
            temperature += 0.25

        # Clamp temperature dans les limites acceptables
        temperature = max(0.1, min(temperature, 2.5))

        # Étape 4 : Préparer prompt avec constraint token
        constraint_token = sector_config.get('constraintToken', '')
        enhanced_prompt = (constraint_token + req.prompt) if constraint_token else req.prompt

        # Étape 5 : Génération
        result = service.generate(
            prompt=enhanced_prompt,
            secteur=req.category,
            generation_type=req.type.value,
            langue=req.langue,
            n=req.n,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            seed=req.seed,
        )

        return GenerateResponse(
            noms=result["noms"],
            strategy_used=result.get("strategy", "nlu"),
            category_hint=sector_config.get("promptHint", ""),
            duree_ms=round((time.time() - t0) * 1000, 1),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))