import time
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User
from ..security import make_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
_FAILS: dict[str, list[float]] = {}
WINDOW, LIMIT = 900, 8  # 8 failed attempts per 15 minutes per user+IP


class LoginIn(BaseModel):
    user_id: str
    password: str


@router.post("/login")
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    uid = body.user_id.strip()
    key = f"{uid.lower()}|{request.client.host if request.client else ''}"
    now = time.time()
    fails = [t for t in _FAILS.get(key, []) if now - t < WINDOW]
    if len(fails) >= LIMIT:
        raise HTTPException(429, "Too many failed attempts. Please try again in a few minutes.")
    user = db.scalar(select(User).where(User.user_id == uid))
    if not user or not verify_password(body.password, user.password_hash):
        fails.append(now)
        _FAILS[key] = fails
        raise HTTPException(401, "Incorrect User ID or password.")
    _FAILS.pop(key, None)
    return {"token": make_token(user), "role": user.role, "name": user.name, "user_id": user.user_id}
