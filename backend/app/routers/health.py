from fastapi import APIRouter
from app.models.schemas import HealthResponse
import os

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health():
    weights = os.path.join(os.path.dirname(__file__), "..", "weights")
    models  = [f for f in os.listdir(weights) if f.endswith(".pt")] if os.path.exists(weights) else []
    return HealthResponse(status="ok", version="2.0.0", models=models)
