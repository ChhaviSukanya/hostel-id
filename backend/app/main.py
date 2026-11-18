from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from .config import get_settings
from .db import Base, SessionLocal, engine
from .models import GenerationRun, User
from .routers import admin, auth, student
from .security import hash_password, verify_password

settings = get_settings()


def _startup():
    if settings.secret_key == "change-me" and not settings.database_url.startswith("sqlite"):
        raise RuntimeError("Set a long random SECRET_KEY in the environment before running in production.")
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        adm = db.scalar(select(User).where(User.role == "admin"))
        if not adm:
            if not settings.admin_password:
                raise RuntimeError("Set ADMIN_PASSWORD to create the first admin account.")
            db.add(User(user_id=settings.admin_user_id, name="Administrator", role="admin",
                        password_hash=hash_password(settings.admin_password)))
        elif settings.admin_password and not verify_password(settings.admin_password, adm.password_hash):
            adm.password_hash = hash_password(settings.admin_password)  # env var is the source of truth
        for run in db.scalars(select(GenerationRun).where(GenerationRun.status == "running")):
            run.status, run.message, run.finished_at = "failed", "Interrupted by a server restart.", datetime.utcnow()
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _startup()
    yield


app = FastAPI(title="Hostel ID Card System", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
                   allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def security_headers(request, call_next):
    resp = await call_next(request)
    resp.headers.update({"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY",
                         "Referrer-Policy": "same-origin"})
    return resp


for r in (auth.router, student.router, admin.router):
    app.include_router(r, prefix="/api")

dist = Path(settings.frontend_dist).resolve()
if (dist / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api"):
            raise HTTPException(404)
        f = (dist / path).resolve()
        if path and f.is_file() and f.is_relative_to(dist):
            return FileResponse(f)
        return FileResponse(dist / "index.html")
