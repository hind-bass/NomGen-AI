"""
Service d'authentification JWT.
- Hash des mots de passe avec bcrypt (passlib)
- Génération et vérification des tokens HS256 (python-jose)
"""
import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

# ─── Configuration ───────────────────────────────────────────────────────────
# En production, mettre cette valeur dans une variable d'environnement .env
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "nomgen-super-secret-key-changez-moi-en-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 heures

# Contexte de hachage bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─── Mots de passe ───────────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """Retourne le hash bcrypt du mot de passe."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe correspond au hash stocké."""
    return pwd_context.verify(plain_password, hashed_password)


# ─── JWT ─────────────────────────────────────────────────────────────────────

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crée un token JWT signé.
    data doit contenir au minimum {"sub": user_email, "role": "user"|"admin"}
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """
    Décode et valide le token JWT.
    Retourne le payload dict ou None si invalide/expiré.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
