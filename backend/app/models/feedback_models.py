"""
Modèles SQLAlchemy/SQLModel pour le système de feedback et votes.

Tables :
  - generations : chaque nom généré est persisté individuellement
  - feedback    : likes et dislikes liés à une génération
  - favoris     : noms marqués comme favoris par les utilisateurs
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Generation(SQLModel, table=True):
    """Enregistrement d'un nom généré avec son contexte complet."""

    __tablename__ = "generations"

    id: Optional[int] = Field(default=None, primary_key=True)
    prompt: str = Field(description="Prompt utilisateur ayant produit ce nom")
    langue: str = Field(max_length=5, index=True)
    categorie: str = Field(index=True, description="Secteur / catégorie (TECH, LUXE, etc.)")
    type_nom: str = Field(default="marque", description="'marque' ou 'societe'")
    nom_genere: str = Field(index=True)
    score: float = Field(default=0.0, description="Score heuristique du nom")
    mode: str = Field(default="A", description="Mode de génération : A (nanoGPT) ou B (LLM)")
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class Feedback(SQLModel, table=True):
    """Vote utilisateur (like ou dislike) sur une génération."""

    __tablename__ = "feedback"

    id: Optional[int] = Field(default=None, primary_key=True)
    generation_id: int = Field(foreign_key="generations.id", index=True)
    vote_type: str = Field(index=True, description="'like' ou 'dislike'")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Favori(SQLModel, table=True):
    """Nom ajouté aux favoris (table dédiée au système de votes)."""

    __tablename__ = "favoris"

    id: Optional[int] = Field(default=None, primary_key=True)
    generation_id: int = Field(foreign_key="generations.id", index=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    nom: str
    langue: str = Field(default="fr")
    categorie: str = Field(default="GENERAL")
    type_nom: str = Field(default="marque")
    created_at: datetime = Field(default_factory=datetime.utcnow)
