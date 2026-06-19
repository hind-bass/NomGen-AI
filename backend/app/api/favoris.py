"""
Routes API — Favoris (table `favoris`).

Endpoints :
  POST /favorites/add
  GET  /favorites
"""
from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from sqlmodel import Session

from app.database import get_session
from app.schemas.feedback_schemas import FavoriAddRequest, FavoriRead
from app.services.auth_service import decode_token
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/favorites", tags=["Favoris (votes)"])


def _get_optional_user_id(request: Request) -> Optional[int]:
    """Extrait user_id du JWT si présent."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    payload = decode_token(token)
    if payload:
        return payload.get("user_id")
    return None


@router.post("/add", status_code=status.HTTP_201_CREATED, response_model=FavoriRead)
def add_favori(
    req: FavoriAddRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    """Ajoute une génération aux favoris."""
    service = FeedbackService(session)
    user_id = _get_optional_user_id(request)
    favori = service.add_favori(req.generation_id, user_id=user_id)
    return favori


@router.get("", response_model=list[FavoriRead])
def list_favoris(
    request: Request,
    session: Session = Depends(get_session),
):
    """Liste les favoris (filtrés par utilisateur si JWT fourni)."""
    service = FeedbackService(session)
    user_id = _get_optional_user_id(request)
    favoris = service.list_favoris(user_id=user_id)
    return favoris
