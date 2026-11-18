"""Google Drive / Sheets helpers. Uses OAuth credentials of the department Google account,
so every file is owned by the same account that runs the Apps Script."""
from datetime import datetime
from functools import lru_cache
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from .config import get_settings

SCOPES = ["https://www.googleapis.com/auth/drive"]


def configured() -> bool:
    s = get_settings()
    return all([s.google_client_id, s.google_client_secret, s.google_refresh_token, s.drive_folder_id])


def script_configured() -> bool:
    s = get_settings()
    return bool(s.apps_script_url and s.apps_script_secret)


@lru_cache
def _creds() -> Credentials:
    s = get_settings()
    return Credentials(
        None, refresh_token=s.google_refresh_token, client_id=s.google_client_id,
        client_secret=s.google_client_secret, token_uri="https://oauth2.googleapis.com/token", scopes=SCOPES,
    )


def warm() -> None:
    _creds().refresh(Request())


def _svc(name: str, version: str):
    return build(name, version, credentials=_creds(), cache_discovery=False)


def link(file_id: str | None) -> str:
    """Same link format Google Forms produces, which the Apps Script already parses."""
    return f"https://drive.google.com/open?id={file_id}" if file_id else ""


def upload_image(path, name: str) -> str:
    media = MediaFileUpload(str(path), mimetype="image/jpeg", resumable=False)
    body = {"name": name, "parents": [get_settings().drive_folder_id]}
    return _svc("drive", "v3").files().create(body=body, media_body=media, fields="id").execute(num_retries=3)["id"]


def create_sheet(values: list[list[str]]) -> str:
    svc = _svc("sheets", "v4")
    title = "Hostel ID data " + datetime.now().strftime("%Y-%m-%d %H:%M")
    body = {
        "properties": {"title": title},
        "sheets": [{"properties": {"title": "Students", "gridProperties": {
            "rowCount": max(100, len(values) + 20), "columnCount": max(13, len(values[0]))}}}],
    }
    sid = svc.spreadsheets().create(body=body, fields="spreadsheetId").execute(num_retries=3)["spreadsheetId"]
    svc.spreadsheets().values().update(
        spreadsheetId=sid, range="Students!A1", valueInputOption="RAW", body={"values": values}
    ).execute(num_retries=3)
    return sid


def download_file(file_id: str, dest) -> None:
    req = _svc("drive", "v3").files().get_media(fileId=file_id)
    with open(dest, "wb") as fh:
        dl = MediaIoBaseDownload(fh, req, chunksize=8 * 1024 * 1024)
        done = False
        while not done:
            _, done = dl.next_chunk(num_retries=3)
