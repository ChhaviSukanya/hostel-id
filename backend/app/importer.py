import io
import re
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import get_settings
from .models import User
from .security import hash_many

ALIASES = {
    "name": {"name", "student name", "full name"},
    "user_id": {"user id", "userid", "user_id", "username", "enrollment no.", "enrollment no", "enrollment number", "enrollment", "enrolment no.", "enrolment no"},
    "password": {"password", "initial password", "pwd"},
}


def _norm(h) -> str:
    return re.sub(r"\s+", " ", str(h).strip().lower())


def _read(data: bytes, filename: str) -> pd.DataFrame:
    name = filename.lower()
    try:
        if name.endswith(".csv"):
            return pd.read_csv(io.BytesIO(data), dtype=str, keep_default_na=False)
        if name.endswith((".xlsx", ".xls")):
            return pd.read_excel(io.BytesIO(data), dtype=str, keep_default_na=False)
    except Exception:
        raise ValueError("The file could not be read. Upload a valid .xlsx, .xls or .csv file.")
    raise ValueError("Upload an Excel file (.xlsx or .xls) or a .csv file.")


def import_students(db: Session, data: bytes, filename: str) -> dict:
    df = _read(data, filename)
    cols = {}
    for col in df.columns:
        for key, names in ALIASES.items():
            if _norm(col) in names and key not in cols:
                cols[key] = col
    missing = [k for k in ("name", "user_id", "password") if k not in cols]
    if missing:
        pretty = {"name": "Name", "user_id": "Enrollment No. (User ID)", "password": "Password"}
        raise ValueError("Missing column(s): " + ", ".join(pretty[m] for m in missing) + ".")

    admin_id = get_settings().admin_user_id.lower()
    existing = set(db.scalars(select(User.user_id)).all())
    seen, good, rejected = set(), [], []

    for i, row in df.iterrows():
        rownum = i + 2  # header is row 1
        name = re.sub(r"\s+", " ", str(row[cols["name"]])).strip()
        uid = re.sub(r"\.0$", "", str(row[cols["user_id"]]).strip())
        pw = str(row[cols["password"]]).strip()
        if not (name or uid or pw):
            continue  # blank line
        reason = None
        if not name or not uid or not pw:
            reason = "Name, User ID and Password are all required."
        elif not re.fullmatch(r"[A-Za-z0-9._-]{3,50}", uid):
            reason = "User ID must be 3-50 letters, digits, '.', '_' or '-'."
        elif uid.lower() == admin_id:
            reason = "This User ID is reserved."
        elif len(pw) < 6 or len(pw.encode()) > 72:
            reason = "Password must be 6 to 72 characters."
        elif len(name) > 150:
            reason = "Name is too long."
        elif uid in seen:
            reason = "Duplicate User ID in this file."
        elif uid in existing:
            reason = "An account with this User ID already exists."
        if reason:
            rejected.append({"row": rownum, "user_id": uid, "reason": reason})
            continue
        seen.add(uid)
        good.append((name, uid, pw))

    if good:
        hashes = hash_many([g[2] for g in good])
        db.add_all([User(user_id=u, name=n, password_hash=h, role="student") for (n, u, _), h in zip(good, hashes)])
        db.commit()
    return {"imported": len(good), "rejected_count": len(rejected), "rejected": rejected[:500]}
