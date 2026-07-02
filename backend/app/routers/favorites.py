"""
Routes CRUD pour les favoris persistants.
GET    /api/favorites       — lister les favoris de l'utilisateur connecté
POST   /api/favorites       — ajouter un favori
DELETE /api/favorites/{id}  — supprimer un favori
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import get_current_user
from app.models.db_models import Favorite, User

router = APIRouter(prefix="/api/favorites", tags=["Favoris"])


# Schémas 

class FavoriteCreate(BaseModel):
    nom: str
    score: float = 0.0
    langue: str = "fr"
    secteur: str = "GENERAL"


class FavoriteRead(BaseModel):
    id: int
    nom: str
    score: float
    langue: str
    secteur: str


#  Endpoints

@router.get("/", response_model=list[FavoriteRead])
def get_favorites(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Retourne tous les favoris de l'utilisateur connecté."""
    favorites = session.exec(
        select(Favorite).where(Favorite.user_id == current_user.id)
    ).all()
    return favorites


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=FavoriteRead)
def add_favorite(
    req: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Ajouter un favori.
    Retourne 409 si ce nom est déjà dans les favoris de l'utilisateur.
    """
    existing = session.exec(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.nom == req.nom,
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{req.nom}' est déjà dans vos favoris.",
        )

    fav = Favorite(
        user_id=current_user.id,
        nom=req.nom,
        score=req.score,
        langue=req.langue,
        secteur=req.secteur,
    )
    session.add(fav)
    session.commit()
    session.refresh(fav)
    return fav


@router.delete("/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_favorite(
    favorite_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Supprimer un favori (vérifie que l'utilisateur en est le propriétaire)."""
    fav = session.get(Favorite, favorite_id)

    if not fav:
        raise HTTPException(status_code=404, detail="Favori non trouvé.")

    if fav.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès interdit.")

    session.delete(fav)
    session.commit()
