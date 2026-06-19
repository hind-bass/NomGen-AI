"""
Schémas Pydantic pour les endpoints feedback et favoris.
Validation stricte des entrées (langue, type_nom, generation_id, etc.).
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


ALLOWED_LANGUES = {"fr", "ar", "en"}
ALLOWED_TYPES = {"marque", "societe"}


class FeedbackActionRequest(BaseModel):
    """Corps des requêtes POST /feedback/like et /feedback/dislike."""

    generation_id: int = Field(..., ge=1, description="ID de la génération votée")

    @field_validator("generation_id")
    @classmethod
    def validate_generation_id(cls, value: int) -> int:
        if value < 1:
            raise ValueError("generation_id doit être un entier positif.")
        return value


class FavoriAddRequest(BaseModel):
    """Corps de POST /favorites/add."""

    generation_id: int = Field(..., ge=1, description="ID de la génération à favoriser")

    @field_validator("generation_id")
    @classmethod
    def validate_generation_id(cls, value: int) -> int:
        if value < 1:
            raise ValueError("generation_id doit être un entier positif.")
        return value


class GenerationRead(BaseModel):
    """Représentation d'une génération enregistrée."""

    id: int
    prompt: str
    langue: str
    categorie: str
    type_nom: str
    nom_genere: str
    score: float
    mode: str
    created_at: datetime


class FavoriRead(BaseModel):
    """Favori retourné par GET /favorites."""

    id: int
    generation_id: int
    nom: str
    langue: str
    categorie: str
    type_nom: str
    created_at: datetime


class NameScoreItem(BaseModel):
    """Nom avec son score agrégé (likes - dislikes)."""

    generation_id: int
    nom_genere: str
    langue: str
    categorie: str
    type_nom: str
    likes: int
    dislikes: int
    score: int = Field(description="likes - dislikes")


class VoteStatsItem(BaseModel):
    """Statistiques de votes pour un nom."""

    generation_id: int
    nom_genere: str
    likes: int
    dislikes: int
    score: int


class FeedbackStatsResponse(BaseModel):
    """Réponse de GET /feedback/stats."""

    total_generations: int
    total_likes: int
    total_dislikes: int
    score_global: int = Field(description="total_likes - total_dislikes")
    plus_apprecies: list[NameScoreItem]
    plus_rejetes: list[NameScoreItem]
    par_langue: dict[str, dict[str, int]]
    par_categorie: dict[str, dict[str, int]]


class FeedbackActionResponse(BaseModel):
    """Réponse après un like ou dislike."""

    message: str
    generation_id: int
    vote_type: Literal["like", "dislike"]
    likes: int
    dislikes: int
    score: int
