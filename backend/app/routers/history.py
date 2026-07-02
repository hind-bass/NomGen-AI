"""
Routes pour l'historique des générations.
GET  /api/history           — historique paginé de l'utilisateur
POST /api/history           — enregistrer une génération (appelé en interne)
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import get_current_user
from app.models.db_models import History, User

router = APIRouter(prefix="/api/history", tags=["Historique"])


# Schémas 
class HistoryRead(BaseModel):
    id: int
    prompt: str
    langue: str
    secteur: str
    n_generated: int
    mode: str
    created_at: str


#  Endpoints 
@router.get("/", response_model=list[HistoryRead])
def get_history(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Retourne l'historique paginé des générations de l'utilisateur.
    Exemple : GET /api/history?limit=10&offset=0
    """
    records = session.exec(
        select(History)
        .where(History.user_id == current_user.id)
        .order_by(History.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return [
        HistoryRead(
            id=r.id,
            prompt=r.prompt,
            langue=r.langue,
            secteur=r.secteur,
            n_generated=r.n_generated,
            mode=r.mode,
            created_at=r.created_at.isoformat(),
        )
        for r in records
    ]


#  Fonction utilitaire interne 
def log_generation(
    session: Session,
    user_id: int,
    prompt: str,
    langue: str,
    secteur: str,
    n_generated: int,
    mode: str = "A",
):
    """
    Enregistre une génération dans l'historique.
    Appelez cette fonction depuis le router /api/generate après une génération réussie.
    """
    record = History(
        user_id=user_id,
        prompt=prompt,
        langue=langue,
        secteur=secteur,
        n_generated=n_generated,
        mode=mode,
    )
    session.add(record)
    session.commit()
