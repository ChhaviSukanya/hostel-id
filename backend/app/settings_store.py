import re
from sqlalchemy.orm import Session
from .models import Setting

DEFAULTS = {
    "validity": "",
    "template_slides_id": "",
    "hostels": "Krishna",
    "programs": "B.Tech CSE\nB.Tech CSE-CYSec\nB.Tech ECE AI\nM.Tech ECE-VLSI\nB.Tech(MAE)+MBA Mechanical",
}
YEARS = [1, 2, 3, 4, 5]


def get(db: Session, key: str) -> str:
    row = db.get(Setting, key)
    return row.value if row else DEFAULTS.get(key, "")


def put(db: Session, key: str, value: str) -> None:
    row = db.get(Setting, key)
    if row:
        row.value = value
    else:
        db.add(Setting(key=key, value=value))


def get_list(db: Session, key: str) -> list[str]:
    return [x.strip() for x in get(db, key).split("\n") if x.strip()]


def parse_slides_id(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    m = re.search(r"/d/([-\w]{25,})", text) or re.fullmatch(r"([-\w]{25,})", text)
    if not m:
        raise ValueError("Enter the Google Slides link (or file ID) of the ID card template.")
    return m.group(1)
