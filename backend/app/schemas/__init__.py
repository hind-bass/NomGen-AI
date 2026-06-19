"""Schémas Pydantic pour l'API de feedback et favoris."""

from app.schemas.feedback_schemas import (
    FeedbackActionRequest,
    FeedbackStatsResponse,
    FavoriAddRequest,
    FavoriRead,
    GenerationRead,
    NameScoreItem,
    VoteStatsItem,
)

__all__ = [
    "FeedbackActionRequest",
    "FeedbackStatsResponse",
    "FavoriAddRequest",
    "FavoriRead",
    "GenerationRead",
    "NameScoreItem",
    "VoteStatsItem",
]
