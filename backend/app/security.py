from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import get_settings
from .db import get_db
from .models import User


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode()[:72], bcrypt.gensalt(rounds=10)).decode()


def hash_many(passwords: list[str]) -> list[str]:
    with ThreadPoolExecutor(max_workers=8) as ex:  # bcrypt releases the GIL
        return list(ex.map(hash_password, passwords))


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode()[:72], hashed.encode())
    except ValueError:
        return False


def make_token(user: User) -> str:
    s = get_settings()
    exp = datetime.now(timezone.utc) + timedelta(minutes=s.token_minutes)
    return jwt.encode({"sub": user.user_id, "role": user.role, "exp": exp}, s.secret_key, "HS256")


_bearer = HTTPBearer(auto_error=False)


def current_user(creds: HTTPAuthorizationCredentials = Depends(_bearer), db: Session = Depends(get_db)) -> User:
    if not creds:
        raise HTTPException(401, "Not signed in.")
    try:
        data = jwt.decode(creds.credentials, get_settings().secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Your session has expired. Please sign in again.")
    user = db.scalar(select(User).where(User.user_id == data.get("sub")))
    if not user or user.role != data.get("role"):
        raise HTTPException(401, "Please sign in again.")
    return user


def admin_only(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(403, "Admin access only.")
    return user


def student_only(user: User = Depends(current_user)) -> User:
    if user.role != "student":
        raise HTTPException(403, "Student access only.")
    return user
