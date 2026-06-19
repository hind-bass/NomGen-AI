"""
Package database — configuration SQLite et initialisation des tables.

Structure :
  database/
    __init__.py      → exports publics (engine, get_session, create_db_and_tables)
    connection.py    → moteur SQLAlchemy / SQLModel
    init_db.py       → script de création + données d'exemple
"""
from app.database.connection import (
    DATABASE_URL,
    create_db_and_tables,
    engine,
    get_session,
)

__all__ = [
    "DATABASE_URL",
    "create_db_and_tables",
    "engine",
    "get_session",
]
