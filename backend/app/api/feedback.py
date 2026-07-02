"""
Routes API  Feedback (likes / dislikes / statistiques).

Endpoints :
  POST /feedback/like
  POST /feedback/dislike
  GET  /feedback/stats
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import Session

from app.database import get_session
from app.schemas.feedback_schemas import (
    FeedbackActionRequest,
    FeedbackActionResponse,
    FeedbackStatsResponse,
)
from app.services.auth_service import decode_token
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["Feedback"])


def _get_optional_user_id(request: Request) -> Optional[int]:
    """Extrait user_id du JWT si présent """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    payload = decode_token(token)
    if payload:
        return payload.get("user_id")
    return None


@router.post("/like", response_model=FeedbackActionResponse)
def like_generation(
    req: FeedbackActionRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    """Enregistre un like sur une génération."""
    service = FeedbackService(session)
    user_id = _get_optional_user_id(request)
    stats = service.add_vote(req.generation_id, "like", user_id=user_id)
    return FeedbackActionResponse(
        message="Like enregistré.",
        generation_id=stats.generation_id,
        vote_type="like",
        likes=stats.likes,
        dislikes=stats.dislikes,
        score=stats.score,
    )


@router.post("/dislike", response_model=FeedbackActionResponse)
def dislike_generation(
    req: FeedbackActionRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    """Enregistre un dislike sur une génération."""
    service = FeedbackService(session)
    user_id = _get_optional_user_id(request)
    stats = service.add_vote(req.generation_id, "dislike", user_id=user_id)
    return FeedbackActionResponse(
        message="Dislike enregistré.",
        generation_id=stats.generation_id,
        vote_type="dislike",
        likes=stats.likes,
        dislikes=stats.dislikes,
        score=stats.score,
    )


@router.get("/stats", response_model=FeedbackStatsResponse)
def feedback_stats(
    top_n: int = Query(default=5, ge=1, le=50, description="Nombre de noms dans les tops"),
    session: Session = Depends(get_session),
):
    """
    Statistiques agrégées :
    - totaux likes / dislikes
    - noms les plus appréciés et rejetés
    - répartition par langue et catégorie
    """
    service = FeedbackService(session)
    return service.get_stats(top_n=top_n)
