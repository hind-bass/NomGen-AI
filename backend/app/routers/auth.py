"""
Routes d'authentification.
POST /auth/register  — créer un compte
POST /auth/login     — obtenir un token JWT
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

from app.database import get_session
from app.models.db_models import User
from app.services.auth_service import (
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentification"])


# Schémas Pydantic (corps des requêtes/réponses) 

class RegisterRequest(BaseModel):
    email: str          
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str


#  Endpoints 

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, session: Session = Depends(get_session)):
    """
    Créer un nouveau compte utilisateur.
    Retourne une 409 si l'email est déjà utilisé.
    """
    existing = session.exec(
        select(User).where(User.email == req.email)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte avec cet email existe déjà.",
        )

    # Validation minimale du mot de passe
    if len(req.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le mot de passe doit contenir au moins 6 caractères.",
        )

    new_user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        role="user",
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return {"message": "Compte créé avec succès.", "email": new_user.email}


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, session: Session = Depends(get_session)):
    """
    Connexion — retourne un token JWT valide 24h.
    """
    user = session.exec(
        select(User).where(User.email == req.email)
    ).first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte a été désactivé.",
        )

    token = create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": user.id}
    )

    return TokenResponse(
        access_token=token,
        role=user.role,
        email=user.email,
    )
