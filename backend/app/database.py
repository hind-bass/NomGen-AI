"""
Configuration SQLite + SQLModel.
Un seul fichier nomgen.db créé au démarrage dans le dossier backend/.
"""
from sqlmodel import SQLModel, create_engine, Session

# SQLite : le fichier est créé automatiquement s'il n'existe pas
DATABASE_URL = "sqlite:///./nomgen.db"

# check_same_thread=False obligatoire pour FastAPI (multi-threading)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # Passer à True pour voir les requêtes SQL dans les logs
)


def create_db_and_tables():
    """Créer toutes les tables au démarrage si elles n'existent pas."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dépendance FastAPI — fournit une session DB par requête."""
    with Session(engine) as session:
        yield session
