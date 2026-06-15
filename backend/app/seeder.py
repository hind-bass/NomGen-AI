"""
Seeder : crée un utilisateur admin par défaut au démarrage si absent.
Identifiants par défaut (à changer en production via variables d'env).
"""
import os
from sqlmodel import Session, select

from app.database import engine
from app.models.db_models import User
from app.services.auth_service import hash_password

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@nomgen.ai")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123456")


def seed_admin():
    """
    Vérifie si un admin existe déjà.
    Si non, en crée un avec les identifiants par défaut.
    Appelé une seule fois dans main.py au démarrage de l'API.
    """
    with Session(engine) as session:
        existing = session.exec(
            select(User).where(User.email == ADMIN_EMAIL)
        ).first()

        if not existing:
            admin = User(
                email=ADMIN_EMAIL,
                hashed_password=hash_password(ADMIN_PASSWORD),
                role="admin",
            )
            session.add(admin)
            session.commit()
            print(f"[Seeder] Admin créé : {ADMIN_EMAIL}")
        else:
            print(f"[Seeder] Admin déjà présent : {ADMIN_EMAIL}")
