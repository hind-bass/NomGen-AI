from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
import json
from app.models.db import get_session, Favorite, History
from app.services.auth_service import decode_token

router = APIRouter()

def get_user_id(authorization: str = Header(...)) -> int:
    try:
        token = authorization.replace("Bearer ", "")
        return int(decode_token(token)["sub"])
    except Exception:
        raise HTTPException(401, detail="Non autorisé")

# ── Favoris ─────────────────────────────────────────────────
class FavoriteIn(BaseModel):
    nom:     str
    secteur: str
    langue:  str
    score:   Optional[float] = 0.0

@router.get("/favorites")
def list_favorites(user_id: int = Depends(get_user_id),
                   db: Session = Depends(get_session)):
    favs = db.exec(select(Favorite).where(Favorite.user_id == user_id)).all()
    return favs

@router.post("/favorites")
def add_favorite(fav: FavoriteIn,
                 user_id: int = Depends(get_user_id),
                 db: Session = Depends(get_session)):
    # Vérifier doublon
    existing = db.exec(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.nom == fav.nom)
    ).first()
    if existing:
        return existing
    new_fav = Favorite(**fav.dict(), user_id=user_id)
    db.add(new_fav)
    db.commit()
    db.refresh(new_fav)
    return new_fav

@router.delete("/favorites/{fav_id}")
def delete_favorite(fav_id: int,
                    user_id: int = Depends(get_user_id),
                    db: Session = Depends(get_session)):
    fav = db.get(Favorite, fav_id)
    if not fav or fav.user_id != user_id:
        raise HTTPException(404)
    db.delete(fav)
    db.commit()
    return {"ok": True}

# ── Historique ───────────────────────────────────────────────
class HistoryIn(BaseModel):
    prompt:  str = ""
    langue:  str
    secteur: str
    noms:    list

@router.post("/history")
def save_history(h: HistoryIn,
                 user_id: int = Depends(get_user_id),
                 db: Session = Depends(get_session)):
    entry = History(
        user_id=user_id, prompt=h.prompt,
        langue=h.langue,  secteur=h.secteur,
        noms_json=json.dumps(h.noms, ensure_ascii=False)
    )
    db.add(entry)
    db.commit()
    return {"ok": True}

@router.get("/history")
def get_history(user_id: int = Depends(get_user_id),
                db: Session = Depends(get_session)):
    entries = db.exec(
        select(History).where(History.user_id == user_id)
        .order_by(History.created_at.desc()).limit(20)
    ).all()
    return [{"id": e.id, "prompt": e.prompt, "langue": e.langue,
             "secteur": e.secteur, "noms": json.loads(e.noms_json),
             "created_at": e.created_at} for e in entries]