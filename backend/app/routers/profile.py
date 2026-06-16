"""
Route de profil utilisateur.
GET /api/profile  — statistiques personnelles de l'utilisateur connecté
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select, func

from app.database import get_session
from app.dependencies import get_current_user
from app.models.db_models import Favorite, History, Suggestion, Reservation, User

router = APIRouter(prefix="/api/profile", tags=["Profil"])


class ProfileResponse(BaseModel):
    email: str
    role: str
    membre_depuis: str
    nb_generations: int
    nb_favoris: int
    nb_suggestions: int
    nb_reservations: int
    nb_suggestions_approuvees: int


@router.get("/", response_model=ProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Retourne les statistiques complètes de l'utilisateur connecté.
    Utilisé pour la page "Mon Profil" du frontend.
    """
    # Compter les générations (historique)
    nb_gen = session.exec(
        select(func.count(History.id)).where(History.user_id == current_user.id)
    ).one()

    # Compter les favoris
    nb_fav = session.exec(
        select(func.count(Favorite.id)).where(Favorite.user_id == current_user.id)
    ).one()

    # Compter les suggestions totales
    nb_sugg = session.exec(
        select(func.count(Suggestion.id)).where(Suggestion.user_id == current_user.id)
    ).one()

    # Compter les suggestions approuvées
    nb_sugg_ok = session.exec(
        select(func.count(Suggestion.id)).where(
            Suggestion.user_id == current_user.id,
            Suggestion.status == "approved",
        )
    ).one()

    # Compter les réservations
    nb_resa = session.exec(
        select(func.count(Reservation.id)).where(Reservation.user_id == current_user.id)
    ).one()

    return ProfileResponse(
        email=current_user.email,
        role=current_user.role,
        membre_depuis=current_user.created_at.strftime("%d/%m/%Y"),
        nb_generations=nb_gen or 0,
        nb_favoris=nb_fav or 0,
        nb_suggestions=nb_sugg or 0,
        nb_reservations=nb_resa or 0,
        nb_suggestions_approuvees=nb_sugg_ok or 0,
    )