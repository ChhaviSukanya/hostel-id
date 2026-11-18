"""End-to-end smoke test (SQLite, Google calls mocked). Run: pytest -q"""
import io, os, tempfile
tmp = tempfile.mkdtemp()
os.environ.update(DATABASE_URL=f"sqlite:///{tmp}/t.db", DATA_DIR=tmp, ADMIN_PASSWORD="Admin@12345", FRONTEND_DIST="/nonexistent")

import pandas as pd
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from PIL import Image
from app import drive
from app.main import app


def img(fmt="PNG"):
    b = io.BytesIO(); Image.new("RGB", (300, 400), "red").save(b, fmt); b.seek(0); return b


def test_full_flow(monkeypatch):
    monkeypatch.setattr(drive, "configured", lambda: True)
    monkeypatch.setattr(drive, "warm", lambda: None)
    monkeypatch.setattr(drive, "upload_image", lambda path, name: "ID_" + name.replace(".", "_") + "_" + "x" * 20)
    with TestClient(app) as c:
        t = c.post("/api/auth/login", json={"user_id": "admin", "password": "Admin@12345"}).json()["token"]
        A = {"Authorization": f"Bearer {t}"}
        assert c.post("/api/auth/login", json={"user_id": "admin", "password": "bad"}).status_code == 401

        df = pd.DataFrame({"Name": ["Aditi Rao", "Bina", "Aditi Rao", "", "Chitra"],
                           "Enrollment No.": ["02610162026", "04501232026", "02610162026", "1", "00702122026"],
                           "Password": ["secret1", "secret2", "secret3", "x", "abc"]})
        buf = io.BytesIO(); df.to_excel(buf, index=False); buf.seek(0)
        r = c.post("/api/admin/students/upload", headers=A, files={"file": ("s.xlsx", buf)}).json()
        assert r["imported"] == 2 and r["rejected_count"] == 3, r
        again = c.post("/api/admin/students/upload", headers=A, files={"file": ("s.xlsx", io.BytesIO(buf.getvalue()))}).json()
        assert again["imported"] == 0
        assert c.get("/api/admin/stats", headers=A).json() == {"total": 2, "submitted": 0, "pending": 2}

        st = c.post("/api/auth/login", json={"user_id": "02610162026", "password": "secret1"}).json()["token"]
        S = {"Authorization": f"Bearer {st}"}
        assert c.get("/api/admin/stats", headers=S).status_code == 403
        assert c.get("/api/student/me", headers=S).json()["submitted"] is False
        form = dict(father_name="=cmd|' /C calc'!A0", program="B.Tech CSE", year="1", hostel="Krishna", dob="2007-01-18",
                    address="Sarawak Rafiganj Aurangabad Bihar", student_phone="+91 95463 69164", parent_phone="80840 77867")
        bad = c.post("/api/student/submit", headers=S, data={**form, "student_phone": "123"},
                     files={"photo": ("p.png", img()), "signature": ("s.txt", io.BytesIO(b"hello"))})
        assert bad.status_code == 422 and set(bad.json()["detail"]["errors"]) == {"student_phone", "signature"}
        ok = c.post("/api/student/submit", headers=S, data=form, files={"photo": ("p.png", img()), "signature": ("s.jpg", img("JPEG"))})
        assert ok.status_code == 201, ok.text
        assert c.post("/api/student/submit", headers=S, data=form, files={"photo": ("p.png", img()), "signature": ("s.jpg", img("JPEG"))}).status_code == 409
        assert c.get("/api/student/me", headers=S).json()["submitted"] is True
        assert c.get("/api/admin/stats", headers=A).json()["submitted"] == 1
        d = c.get("/api/admin/students/02610162026", headers=A).json()
        assert d["details"]["Student Phone"] == "9546369164"
        assert c.get("/api/admin/students/02610162026/image/photo", headers=A).status_code == 200
        assert len(c.get("/api/admin/students?status=pending", headers=A).json()["items"]) == 1

        assert c.get("/api/admin/generation/excel", headers=A).status_code == 400  # validity missing
        s = c.put("/api/admin/card-settings", headers=A, json={"validity": "2027-05-31", "template": "",
                  "hostels": ["Krishna"], "programs": ["B.Tech CSE"]})
        assert s.status_code == 200
        x = c.get("/api/admin/generation/excel", headers=A)
        assert x.status_code == 200
        ws = load_workbook(io.BytesIO(x.content)).active
        hdr = [c_.value for c_ in ws[1]]
        assert hdr == ["Name", "D/O", "Enrollment No.", "Program", "Year", "Hostel", "DOB", "Validity", "Address",
                       "Student Phone", "Parent Phone", "Student photo", "Student signature"]
        row = [c_.value for c_ in ws[2]]
        assert row[2] == "02610162026" and row[1].startswith("=cmd") and ws["B2"].data_type == "s"
        assert row[11].startswith("https://drive.google.com/open?id=")
        print(row)
