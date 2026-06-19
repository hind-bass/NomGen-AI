"""
Configuration SQLite + SQLModel.
Fichier nomgen.db créé automatiquement dans backend/.
"""
from sqlmodel import SQLModel, Session, create_engine, text

# Import des modèles pour que SQLModel.metadata les enregistre
import app.models.db_models  # noqa: F401
import app.models.feedback_models  # noqa: F401

DATABASE_URL = "sqlite:///./nomgen.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

# Colonnes ajoutées au modèle Reservation (migration légère SQLite)
_RESERVATION_MIGRATIONS = [
    ("forfait", "VARCHAR DEFAULT 'free'"),
    ("client_nom", "VARCHAR"),
    ("client_prenom", "VARCHAR"),
    ("client_email", "VARCHAR"),
    ("card_last4", "VARCHAR"),
    ("card_expiry", "VARCHAR"),
    ("payment_status", "VARCHAR DEFAULT 'pending'"),
]


def _migrate_reservation_columns() -> None:
    """Ajoute les colonnes manquantes à la table reservation (SQLite)."""
    with engine.connect() as conn:
        rows = conn.execute(text("PRAGMA table_info(reservation)")).fetchall()
        existing = {row[1] for row in rows}
        for col_name, col_type in _RESERVATION_MIGRATIONS:
            if col_name not in existing:
                conn.execute(text(f"ALTER TABLE reservation ADD COLUMN {col_name} {col_type}"))
        conn.commit()


def create_db_and_tables() -> None:
    """Crée toutes les tables au démarrage si elles n'existent pas."""
    SQLModel.metadata.create_all(engine)
    _migrate_reservation_columns()


def get_session():
    """Dépendance FastAPI — fournit une session DB par requête."""
    with Session(engine) as session:
        yield session
