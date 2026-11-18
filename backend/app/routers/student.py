from datetime import date
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .. import settings_store as ss
from ..db import get_db
from ..generation import push_one_to_drive
from ..models import Submission, User
from ..security import student_only
from ..storage import delete_file, save_student_image
from ..validators import clean_phone, clean_text

router = APIRouter(prefix="/student", tags=["student"])


def _options(db: Session) -> dict:
    return {"programs": ss.get_list(db, "programs"), "hostels": ss.get_list(db, "hostels"), "years": ss.YEARS}


@router.get("/me")
def me(user: User = Depends(student_only), db: Session = Depends(get_db)):
    return {"user_id": user.user_id, "name": user.name, "submitted": user.submission is not None,
            "options": _options(db)}


@router.post("/submit", status_code=201)
def submit(
    background: BackgroundTasks,
    father_name: str = Form(...), program: str = Form(...), year: int = Form(...), hostel: str = Form(...),
    dob: str = Form(...), address: str = Form(...), student_phone: str = Form(...), parent_phone: str = Form(...),
    photo: UploadFile = File(...), signature: UploadFile = File(...),
    user: User = Depends(student_only), db: Session = Depends(get_db),
):
    if user.submission:
        raise HTTPException(409, "You have already submitted your details.")
    opts, errors = _options(db), {}

    father_name = clean_text(father_name)
    if not 2 <= len(father_name) <= 100:
        errors["father_name"] = "Enter the name (2 to 100 characters)."
    if program not in opts["programs"]:
        errors["program"] = "Select a program from the list."
    if year not in opts["years"]:
        errors["year"] = "Select your year."
    if hostel not in opts["hostels"]:
        errors["hostel"] = "Select your hostel."
    try:
        d = date.fromisoformat(dob)
        age = (date.today() - d).days / 365.25
        if not 15 <= age <= 60:
            errors["dob"] = "Check the date of birth."
    except ValueError:
        d = None
        errors["dob"] = "Enter a valid date of birth."
    address = clean_text(address)
    if not 10 <= len(address) <= 300:
        errors["address"] = "Enter the full address (10 to 300 characters)."
    phones = {}
    for field, val in (("student_phone", student_phone), ("parent_phone", parent_phone)):
        try:
            phones[field] = clean_phone(val)
        except ValueError as e:
            errors[field] = str(e)

    saved = {}
    for field, up, folder in (("photo", photo, "photos"), ("signature", signature, "signatures")):
        try:
            saved[field] = save_student_image(up, folder)
        except ValueError as e:
            errors[field] = str(e)
    if errors:
        for rel in saved.values():
            delete_file(rel)
        raise HTTPException(422, {"errors": errors})

    sub = Submission(user_pk=user.id, father_name=father_name, program=program, year=year, hostel=hostel,
                     dob=d, address=address, student_phone=phones["student_phone"],
                     parent_phone=phones["parent_phone"], photo_file=saved["photo"], signature_file=saved["signature"])
    db.add(sub)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        for rel in saved.values():
            delete_file(rel)
        raise HTTPException(409, "You have already submitted your details.")
    background.add_task(push_one_to_drive, sub.id)
    return {"ok": True}
