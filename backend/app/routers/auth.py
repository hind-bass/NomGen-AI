from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session
from pydantic import BaseModel
from app.models.db import get_session, User
from app.services.auth_service import (
    register_user, get_user_by_email,
    verify_password, create_token, decode_token
)

router = APIRouter()

class AuthRequest(BaseModel):
    email:    str
    password: str

@router.post("/auth/register")
def register(req: AuthRequest, db: Session = Depends(get_session)):
    try:
        user = register_user(db, req.email, req.password)
        return {"token": create_token(user.id, user.role), "email": user.email}
    except ValueError as e:
        raise HTTPException(400, detail=str(e))

@router.post("/auth/login")
def login(req: AuthRequest, db: Session = Depends(get_session)):
    user = get_user_by_email(db, req.email)
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, detail="Email ou mot de passe incorrect")
    return {"token": create_token(user.id, user.role), "email": user.email, "role": user.role}

@router.get("/auth/me")
def me(authorization: str = Header(...), db: Session = Depends(get_session)):
    try:
        token   = authorization.replace("Bearer ", "")
        payload = decode_token(token)
        user    = db.get(User, int(payload["sub"]))
        if not user:
            raise HTTPException(404)
        return {"id": user.id, "email": user.email, "role": user.role}
    except Exception:
        raise HTTPException(401, detail="Token invalide")