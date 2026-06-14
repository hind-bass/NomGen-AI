from sqlmodel import SQLModel, Field, create_engine, Session
from typing import Optional
from datetime import datetime

# ── Tables ──────────────────────────────────────────────────
class User(SQLModel, table=True):
    id:           Optional[int] = Field(default=None, primary_key=True)
    email:        str           = Field(unique=True, index=True)
    password_hash: str
    role:         str           = "user"   # "user" ou "admin"
    created_at:   datetime      = Field(default_factory=datetime.utcnow)

class Favorite(SQLModel, table=True):
    id:        Optional[int] = Field(default=None, primary_key=True)
    user_id:   int           = Field(foreign_key="user.id")
    nom:       str
    secteur:   str
    langue:    str
    score:     float         = 0.0
    saved_at:  datetime      = Field(default_factory=datetime.utcnow)

class History(SQLModel, table=True):
    id:         Optional[int] = Field(default=None, primary_key=True)
    user_id:    int           = Field(foreign_key="user.id")
    prompt:     str           = ""
    langue:     str
    secteur:    str
    noms_json:  str           = "[]"   # JSON stringifié
    created_at: datetime      = Field(default_factory=datetime.utcnow)

class Suggestion(SQLModel, table=True):
    id:          Optional[int] = Field(default=None, primary_key=True)
    user_id:     int           = Field(foreign_key="user.id")
    nom:         str
    categorie:   str
    langue:      str
    statut:      str           = "pending"  # "pending", "approved", "rejected"
    created_at:  datetime      = Field(default_factory=datetime.utcnow)

class Reservation(SQLModel, table=True):
    id:           Optional[int] = Field(default=None, primary_key=True)
    user_id:      int           = Field(foreign_key="user.id")
    nom:          str
    statut:       str           = "active"
    date_debut:   datetime      = Field(default_factory=datetime.utcnow)
    date_fin:     Optional[datetime] = None

# ── Connexion SQLite (fichier local, zéro configuration) ────
DATABASE_URL = "sqlite:///./nomgen.db"
engine = create_engine(DATABASE_URL, echo=False)

def create_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session