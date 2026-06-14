from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.models.db import User

SECRET_KEY = "nomgen-secret-key-change-en-prod"  # changer en prod
ALGORITHM  = "HS256"
EXPIRE_MIN = 60 * 24   # 24 heures

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def create_token(user_id: int, role: str) -> str:
    payload = {
        "sub":  str(user_id),
        "role": role,
        "exp":  datetime.utcnow() + timedelta(minutes=EXPIRE_MIN)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def get_user_by_email(db: Session, email: str):
    return db.exec(select(User).where(User.email == email)).first()

def register_user(db: Session, email: str, password: str) -> User:
    if get_user_by_email(db, email):
        raise ValueError("Email déjà utilisé")
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user