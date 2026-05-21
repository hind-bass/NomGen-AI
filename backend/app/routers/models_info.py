from fastapi import APIRouter

router = APIRouter()

@router.get("/models")
async def models_info():
    return {
        "models": [
            {"id": "nanogpt-fr", "langue": "fr", "version": "3.0",
             "secteurs": ["LUXE","TECH","FOOD","BIO","PHARMA","INDUSTRIE"]},
            {"id": "nanogpt-ar", "langue": "ar", "version": "1.0",
             "secteurs": ["GENERAL"]},
        ]
    }
