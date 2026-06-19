"""
Modèles de base de données SQLModel (SQLite).
Chaque classe = une table. SQLModel combine Pydantic + SQLAlchemy.
"""
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Table des utilisateurs enregistrés."""
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    role: str = Field(default="user")          # "user" | "admin"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)


class Favorite(SQLModel, table=True):
    """Favoris persistants par utilisateur."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    nom: str
    score: float = Field(default=0.0)
    langue: str = Field(default="fr")
    secteur: str = Field(default="GENERAL")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class History(SQLModel, table=True):
    """Historique de chaque requête de génération."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    prompt: str
    langue: str
    secteur: str
    n_generated: int
    mode: str = Field(default="A")             # "A" (nanoGPT) | "B" (LLM)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Suggestion(SQLModel, table=True):
    """Suggestions communautaires soumises par les users."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    nom: str
    langue: str
    secteur: str
    type_nom: str = Field(default="marque")    # "marque" | "societe"
    status: str = Field(default="pending")     # "pending" | "approved" | "rejected"
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None


class Reservation(SQLModel, table=True):
    """Réservation premium d'un nom généré."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    nom: str
    langue: str
    secteur: str
    stripe_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_paid: bool = Field(default=False)
    # Informations client & paiement (demande envoyée à l'admin)
    forfait: str = Field(default="free")              # free | pro | max
    client_nom: Optional[str] = None
    client_prenom: Optional[str] = None
    client_email: Optional[str] = None
    card_last4: Optional[str] = None                  # 4 derniers chiffres uniquement
    card_expiry: Optional[str] = None                 # MM/YY
    payment_status: str = Field(default="pending")    # pending | validated | rejected
