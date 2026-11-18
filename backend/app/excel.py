import io
from datetime import date
from openpyxl import Workbook
from openpyxl.styles import Font
from . import drive

# Exact headers and order expected by the existing Apps Script / sample sheet.
COLUMNS = ["Name", "D/O", "Enrollment No.", "Program", "Year", "Hostel", "DOB", "Validity",
           "Address", "Student Phone", "Parent Phone", "Student photo", "Student signature"]
WIDTHS = [26, 26, 16, 26, 7, 12, 12, 12, 50, 15, 15, 48, 48]


def sheet_values(pairs, validity: date) -> list[list[str]]:
    """Rows for the Google Sheet (all text; dates pre-formatted dd-MM-yyyy, same as the card shows)."""
    rows = [COLUMNS]
    for u, s in pairs:
        rows.append([u.name, s.father_name, u.user_id, s.program, str(s.year), s.hostel,
                     s.dob.strftime("%d-%m-%Y"), validity.strftime("%d-%m-%Y"), s.address,
                     s.student_phone, s.parent_phone, drive.link(s.photo_drive_id), drive.link(s.signature_drive_id)])
    return rows


def build_workbook(pairs, validity: date) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Students"
    ws.append(COLUMNS)
    for c in ws[1]:
        c.font = Font(bold=True)
    for u, s in pairs:
        ws.append([u.name, s.father_name, u.user_id, s.program, s.year, s.hostel, s.dob, validity,
                   s.address, s.student_phone, s.parent_phone, drive.link(s.photo_drive_id), drive.link(s.signature_drive_id)])
        for cell in ws[ws.max_row]:
            if isinstance(cell.value, str):
                cell.data_type = "s"  # never let a value such as "=1+1" become a formula
        r = ws.max_row
        ws.cell(r, 7).number_format = "dd/mm/yyyy"
        ws.cell(r, 8).number_format = "dd/mm/yyyy"
        for col in (3, 10, 11):
            ws.cell(r, col).number_format = "@"  # keep leading zeros
    for i, w in enumerate(WIDTHS, start=1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = w
    ws.freeze_panes = "A2"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
