"""
Routes pour les réservations premium.
POST   /api/reservations          — réserver un nom (génère le lien Stripe)
GET    /api/reservations          — voir ses réservations
DELETE /api/reservations/:id      — annuler une réservation non payée
"""
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import get_current_user
from app.models.db_models import Reservation, User

router = APIRouter(prefix="/api/reservations", tags=["Réservations Premium"])

# Lien Stripe de base (créé depuis le Dashboard Stripe → Payment Links)
# En prod : mettre dans une variable d'env STRIPE_PAYMENT_LINK
STRIPE_BASE_LINK = os.getenv(
    "STRIPE_PAYMENT_LINK",
    "https://buy.stripe.com/test_VOTRE_LIEN_ICI"
)

# Durée de réservation (en jours)
RESERVATION_DURATION_DAYS = 30


# ─── Schémas ─────────────────────────────────────────────────────────────────

class ReservationCreate(BaseModel):
    nom: str
    langue: str = "fr"
    secteur: str = "GENERAL"


class ReservationRead(BaseModel):
    id: int
    nom: str
    langue: str
    secteur: str
    stripe_url: str | None
    expires_at: str | None
    is_paid: bool
    created_at: str


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ReservationRead)
def create_reservation(
    req: ReservationCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Réserver un nom généré (accès premium).
    Retourne un lien Stripe pré-rempli avec l'email et le nom.
    Retourne 409 si ce nom est déjà réservé et payé.
    """
    nom_clean = req.nom.strip()
    if not nom_clean:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le nom ne peut pas être vide."
        )

    # Vérifier si déjà réservé (et payé) par quelqu'un
    existing_paid = session.exec(
        select(Reservation).where(
            Reservation.nom == nom_clean,
            Reservation.is_paid == True,
        )
    ).first()
    if existing_paid:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{nom_clean}' est déjà réservé par un autre utilisateur."
        )

    # Construire l'URL Stripe avec paramètres pré-remplis
    import urllib.parse
    params = urllib.parse.urlencode({
        "prefilled_email": current_user.email,
        "client_reference_id": str(current_user.id),
        "item_name": nom_clean,
    })
    stripe_url = f"{STRIPE_BASE_LINK}?{params}"

    # Date d'expiration de la réservation
    expires_at = datetime.utcnow() + timedelta(days=RESERVATION_DURATION_DAYS)

    reservation = Reservation(
        user_id=current_user.id,
        nom=nom_clean,
        langue=req.langue,
        secteur=req.secteur,
        stripe_url=stripe_url,
        expires_at=expires_at,
        is_paid=False,
    )
    session.add(reservation)
    session.commit()
    session.refresh(reservation)

    return ReservationRead(
        id=reservation.id,
        nom=reservation.nom,
        langue=reservation.langue,
        secteur=reservation.secteur,
        stripe_url=reservation.stripe_url,
        expires_at=reservation.expires_at.isoformat() if reservation.expires_at else None,
        is_paid=reservation.is_paid,
        created_at=reservation.created_at.isoformat(),
    )


@router.get("/", response_model=list[ReservationRead])
def get_my_reservations(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Liste toutes les réservations de l'utilisateur connecté."""
    reservations = session.exec(
        select(Reservation).where(Reservation.user_id == current_user.id)
    ).all()

    return [
        ReservationRead(
            id=r.id,
            nom=r.nom,
            langue=r.langue,
            secteur=r.secteur,
            stripe_url=r.stripe_url,
            expires_at=r.expires_at.isoformat() if r.expires_at else None,
            is_paid=r.is_paid,
            created_at=r.created_at.isoformat(),
        )
        for r in reservations
    ]


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_reservation(
    reservation_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Annuler une réservation non encore payée."""
    reservation = session.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Réservation introuvable.")
    if reservation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé.")
    if reservation.is_paid:
        raise HTTPException(
            status_code=400,
            detail="Impossible d'annuler une réservation déjà payée."
        )
    session.delete(reservation)
    session.commit()