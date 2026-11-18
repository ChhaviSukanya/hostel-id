import json
from datetime import date
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from .. import drive, excel, generation, settings_store as ss
from ..db import get_db
from ..importer import import_students
from ..models import GenerationRun, Submission, User
from ..security import admin_only
from ..storage import data_path, delete_file, save_template_preview

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(admin_only)])


# ---------- 1. Upload students ----------
@router.post("/students/upload")
def upload_students(file: UploadFile = File(...), db: Session = Depends(get_db)):
    data = file.file.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "The file is larger than 5 MB.")
    try:
        return import_students(db, data, file.filename or "")
    except ValueError as e:
        raise HTTPException(400, str(e))


# ---------- 2. Dashboard ----------
@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(User).where(User.role == "student")) or 0
    done = db.scalar(select(func.count()).select_from(Submission)) or 0
    return {"total": total, "submitted": done, "pending": total - done}


@router.get("/students")
def list_students(search: str = "", status: str = "all", page: int = 1, page_size: int = 25,
                  db: Session = Depends(get_db)):
    page, page_size = max(page, 1), min(max(page_size, 1), 200)
    q = (select(User.user_id, User.name, User.created_at, Submission.submitted_at)
         .outerjoin(Submission, Submission.user_pk == User.id).where(User.role == "student"))
    if search.strip():
        like = f"%{search.strip()}%"
        q = q.where(or_(User.name.ilike(like), User.user_id.ilike(like)))
    if status == "submitted":
        q = q.where(Submission.id.is_not(None))
    elif status == "pending":
        q = q.where(Submission.id.is_(None))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.execute(q.order_by(User.user_id).limit(page_size).offset((page - 1) * page_size)).all()
    return {"total": total, "page": page, "page_size": page_size, "items": [
        {"user_id": r.user_id, "name": r.name, "created_at": r.created_at,
         "submitted": r.submitted_at is not None, "submitted_at": r.submitted_at} for r in rows]}


def _student(db: Session, user_id: str) -> User:
    u = db.scalar(select(User).where(User.user_id == user_id, User.role == "student"))
    if not u:
        raise HTTPException(404, "Student not found.")
    return u


@router.get("/students/{user_id}")
def student_detail(user_id: str, db: Session = Depends(get_db)):
    u = _student(db, user_id)
    s = u.submission
    return {"user_id": u.user_id, "name": u.name, "submitted": s is not None, "details": None if not s else {
        "D/O": s.father_name, "Program": s.program, "Year": s.year, "Hostel": s.hostel,
        "DOB": s.dob.strftime("%d-%m-%Y"), "Address": s.address, "Student Phone": s.student_phone,
        "Parent Phone": s.parent_phone, "Submitted at": s.submitted_at.strftime("%d-%m-%Y %H:%M")}}


@router.get("/students/{user_id}/image/{kind}")
def student_image(user_id: str, kind: str, db: Session = Depends(get_db)):
    s = _student(db, user_id).submission
    if kind not in ("photo", "signature") or not s:
        raise HTTPException(404, "Not found.")
    return FileResponse(data_path(getattr(s, f"{kind}_file")), media_type="image/jpeg")


@router.delete("/students/{user_id}/submission")
def reset_submission(user_id: str, db: Session = Depends(get_db)):
    """Lets a student fix a mistake: removes the submission so the form shows again."""
    s = _student(db, user_id).submission
    if not s:
        raise HTTPException(404, "This student has not submitted.")
    files = [s.photo_file, s.signature_file]
    db.delete(s)
    db.commit()
    for f in files:
        delete_file(f)
    return {"ok": True}


# ---------- 3. ID card template and card settings ----------
class CardSettingsIn(BaseModel):
    validity: Optional[date] = None
    template: str = ""
    hostels: list[str]
    programs: list[str]


def _clean_list(items: list[str], label: str) -> list[str]:
    out = list(dict.fromkeys(" ".join(i.split()) for i in items if i.strip()))
    if not out or any(len(i) > 100 for i in out):
        raise HTTPException(422, f"Enter at least one {label} (up to 100 characters each).")
    return out


@router.get("/card-settings")
def get_card_settings(db: Session = Depends(get_db)):
    return {"validity": ss.get(db, "validity") or None, "template_id": ss.get(db, "template_slides_id"),
            "hostels": ss.get_list(db, "hostels"), "programs": ss.get_list(db, "programs"),
            "has_preview": data_path("template", "preview.jpg").exists()}


@router.put("/card-settings")
def put_card_settings(body: CardSettingsIn, db: Session = Depends(get_db)):
    try:
        tid = ss.parse_slides_id(body.template)
    except ValueError as e:
        raise HTTPException(422, str(e))
    ss.put(db, "validity", body.validity.isoformat() if body.validity else "")
    ss.put(db, "template_slides_id", tid)
    ss.put(db, "hostels", "\n".join(_clean_list(body.hostels, "hostel")))
    ss.put(db, "programs", "\n".join(_clean_list(body.programs, "program")))
    db.commit()
    return {"ok": True}


@router.post("/template/preview")
def upload_preview(file: UploadFile = File(...)):
    try:
        save_template_preview(file)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@router.get("/template/preview")
def get_preview():
    p = data_path("template", "preview.jpg")
    if not p.exists():
        raise HTTPException(404, "No template uploaded yet.")
    return FileResponse(p, media_type="image/jpeg", headers={"Cache-Control": "no-cache"})


# ---------- 4. Excel and ID generation ----------
@router.get("/generation/summary")
def gen_summary(db: Session = Depends(get_db)):
    n = db.scalar(select(func.count()).select_from(Submission)) or 0
    return {"submitted": n, "validity_set": bool(ss.get(db, "validity")), "drive_ready": drive.configured(),
            "script_ready": drive.script_configured(), "template_set": bool(ss.get(db, "template_slides_id"))}


def _check_export(db: Session):
    if not ss.get(db, "validity"):
        raise HTTPException(400, "Set the validity date on the ID Card Template page first.")
    if not drive.configured():
        raise HTTPException(400, "Google Drive is not connected. See the setup guide (GOOGLE_* settings).")
    pairs = generation.submitted_pairs(db)
    if not pairs:
        raise HTTPException(400, "No student has submitted the form yet.")
    return pairs


@router.get("/generation/excel")
def download_excel(db: Session = Depends(get_db)):
    pairs = _check_export(db)
    fails = generation.ensure_drive_ids(db, pairs)
    if fails:
        raise HTTPException(502, "Some images could not be uploaded to Drive: " + "; ".join(fails[:3]))
    blob = excel.build_workbook(pairs, generation.get_validity(db))
    name = f"hostel_id_cards_{date.today().isoformat()}.xlsx"
    return Response(blob, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.post("/generation/run", status_code=202)
def run_generation(background: BackgroundTasks, db: Session = Depends(get_db)):
    _check_export(db)
    if not drive.script_configured():
        raise HTTPException(400, "Apps Script is not connected. Set APPS_SCRIPT_URL and APPS_SCRIPT_SECRET.")
    try:
        run = generation.start_run(db)
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    background.add_task(generation.run_job, run.id)
    return {"id": run.id}


def _run_json(r: GenerationRun | None):
    if not r:
        return None
    return {"id": r.id, "status": r.status, "stage": r.stage, "total": r.total, "done": r.done,
            "message": r.message, "warnings": json.loads(r.warnings or "[]"), "slides_url": r.slides_url,
            "has_pdf": bool(r.pdf_file), "created_at": r.created_at, "finished_at": r.finished_at}


@router.get("/generation/latest")
def latest_run(db: Session = Depends(get_db)):
    return _run_json(db.scalar(select(GenerationRun).order_by(GenerationRun.id.desc()).limit(1)))


@router.get("/generation/runs/{run_id}/pdf")
def download_pdf(run_id: int, db: Session = Depends(get_db)):
    r = db.get(GenerationRun, run_id)
    if not r or not r.pdf_file:
        raise HTTPException(404, "PDF not available.")
    return FileResponse(data_path(r.pdf_file), media_type="application/pdf", filename="hostel_id_cards.pdf")
