import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session
from . import drive, excel, settings_store
from .config import get_settings
from .db import SessionLocal
from .models import GenerationRun, Submission, User
from .storage import data_path

BATCH = 25  # students per Apps Script call (keeps each call well under the 6-minute limit)
_lock = threading.Lock()


def submitted_pairs(db: Session):
    q = select(User, Submission).join(Submission, Submission.user_pk == User.id).order_by(User.user_id)
    return [(u, s) for u, s in db.execute(q).all()]


def get_validity(db: Session) -> date | None:
    v = settings_store.get(db, "validity")
    return date.fromisoformat(v) if v else None


def ensure_drive_ids(db: Session, pairs) -> list[str]:
    """Upload any photo/signature not yet on Drive. Returns a list of failure messages."""
    todo = []
    for u, s in pairs:
        if not s.photo_drive_id:
            todo.append((u, s, "photo"))
        if not s.signature_drive_id:
            todo.append((u, s, "signature"))
    if not todo:
        return []
    drive.warm()

    def up(item):
        u, s, kind = item
        try:
            return item, drive.upload_image(data_path(getattr(s, f"{kind}_file")), f"{u.user_id}_{kind}.jpg"), None
        except Exception as e:  # noqa: BLE001
            return item, None, str(e)[:200]

    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(up, todo))
    fails = []
    for (u, s, kind), fid, err in results:
        if fid:
            setattr(s, f"{kind}_drive_id", fid)
        else:
            fails.append(f"{u.user_id} {u.name}: {kind} could not be uploaded to Drive ({err})")
    db.commit()
    return fails


def push_one_to_drive(submission_id: int) -> None:
    """Background task after a student submits: best effort, export step retries failures."""
    if not drive.configured():
        return
    db = SessionLocal()
    try:
        s = db.get(Submission, submission_id)
        if s:
            ensure_drive_ids(db, [(s.user, s)])
    except Exception:  # noqa: BLE001
        pass
    finally:
        db.close()


def _call_script(payload: dict) -> dict:
    s = get_settings()
    payload["secret"] = s.apps_script_secret
    try:
        r = httpx.post(s.apps_script_url, json=payload, timeout=900, follow_redirects=True)
        data = r.json()
    except Exception:  # noqa: BLE001
        raise RuntimeError("Apps Script did not return a valid answer. Check that the Web App is deployed "
                           "with access set to 'Anyone' and that the URL ends in /exec.")
    if not data.get("ok"):
        raise RuntimeError("Apps Script error: " + str(data.get("error", "unknown")))
    return data


def start_run(db: Session) -> GenerationRun:
    with _lock:
        running = db.scalar(select(GenerationRun).where(GenerationRun.status == "running"))
        if running:
            raise RuntimeError("A generation is already in progress.")
        run = GenerationRun(status="running", stage="Starting")
        db.add(run)
        db.commit()
        return run


def run_job(run_id: int) -> None:
    db = SessionLocal()
    run = db.get(GenerationRun, run_id)
    warnings: list[str] = []

    def stage(text: str):
        run.stage = text
        run.warnings = json.dumps(warnings)
        db.commit()

    try:
        pairs = submitted_pairs(db)
        validity = get_validity(db)
        run.total = len(pairs)
        stage("Uploading images to Google Drive")
        warnings += ensure_drive_ids(db, pairs)
        stage("Writing student data to a Google Sheet")
        sheet_id = drive.create_sheet(excel.sheet_values(pairs, validity))
        template = settings_store.get(db, "template_slides_id")
        pid = _call_script({"action": "start", "templateId": template})["presentationId"]
        for i in range(0, len(pairs), BATCH):
            j = min(i + BATCH, len(pairs))
            stage(f"Generating cards {i + 1}-{j} of {len(pairs)}")
            res = _call_script({"action": "batch", "presentationId": pid, "templateId": template,
                                "sheetId": sheet_id, "from": i, "to": j})
            warnings += res.get("errors", [])
            run.done = j
            db.commit()
        stage("Creating the PDF")
        fin = _call_script({"action": "finish", "presentationId": pid, "templateId": template})
        run.slides_url = fin.get("slidesUrl", "")
        stage("Downloading the PDF")
        rel = f"generated/id_cards_{run.id}.pdf"
        drive.download_file(fin["pdfId"], data_path(rel))
        run.pdf_file = rel
        run.status, run.stage = "done", "Finished"
    except Exception as e:  # noqa: BLE001
        db.rollback()
        run.status, run.message = "failed", str(e)[:1000]
    finally:
        run.warnings = json.dumps(warnings[:300])
        run.finished_at = datetime.utcnow()
        db.commit()
        db.close()
