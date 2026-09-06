from fastapi import Depends, Header, HTTPException
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models import User

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd.verify(password, password_hash)
    except Exception:
        return False

def current_user(
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_password: str | None = Header(None, alias="X-User-Password"),
    db: Session = Depends(get_db),
) -> User:
    if settings.demo_disable_auth and not (x_user_email and x_user_password):
        user = db.scalar(select(User).order_by(User.id).limit(1))
        if not user:
            raise HTTPException(401, "No demo user available")
        return user
    if not x_user_email or not x_user_password:
        raise HTTPException(401, "Missing credentials")
    user = db.scalar(select(User).where(User.email == x_user_email.lower().strip()))
    if not user or not verify_password(x_user_password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    return user

def current_admin(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(403, "Admin privileges required")
    return user
