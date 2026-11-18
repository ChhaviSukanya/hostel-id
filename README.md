# Hostel ID Card Management System – IGDTUW

Students log in and fill their ID card details once. The admin monitors submissions, exports the Excel your
Apps Script expects, and generates the ID cards (PDF) with that same script.

**Stack:** React + Tailwind (Vite) · FastAPI · PostgreSQL · Google Drive/Sheets/Apps Script. One server serves both the API and the website, so students use a single URL.

```
backend/      FastAPI app (app/), tests/
frontend/     React + Tailwind
apps-script/  Code.gs – your script, fixed and made callable by the website
scripts/      get_google_token.py (one-time)
```

## 1. Run locally

```bash
cp .env.example .env              # then edit it (SECRET_KEY, ADMIN_PASSWORD; DATABASE_URL for Postgres)

# backend (use DATABASE_URL=sqlite:///./dev.db for a quick try without Postgres)
cd backend
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --env-file ../.env          # http://localhost:8000

# frontend (second terminal)
cd frontend && npm install && npm run dev                 # http://localhost:5173
```
Sign in as the admin with `ADMIN_USER_ID` / `ADMIN_PASSWORD`. Tables are created automatically.

Or with Docker (app + PostgreSQL): `docker compose up --build` → http://localhost:8000

Run the tests: `cd backend && pytest -q`

## 2. Connect Google (needed for Excel export and ID generation)

All Google resources belong to **one department Google account** (the one that owns the template and runs the script).

1. **Google Cloud project** → enable **Google Drive API** and **Google Sheets API**.
2. **OAuth consent screen**: choose *Internal* if the account is a Workspace account, otherwise publish the app (*In production*) –
   apps left in "Testing" have refresh tokens that expire after 7 days. Create an **OAuth client ID** of type *Desktop app*.
3. `python scripts/get_google_token.py <CLIENT_ID> <CLIENT_SECRET>` → sign in with the department account →
   put `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` in `.env`.
4. Create a **Drive folder** for student images. Its ID (the last part of the folder URL) is `DRIVE_FOLDER_ID`.
5. **Apps Script**: open script.google.com (same account) → new project → paste `apps-script/Code.gs`.
   *Project settings → Script properties* → add `API_SECRET` = a long random string (also set as `APPS_SCRIPT_SECRET`).
   *Deploy → New deployment → Web app* → Execute as **Me**, Who has access **Anyone** → copy the URL ending in `/exec` into `APPS_SCRIPT_URL`.
   Authorize the permissions when asked. After any later edit to the script, use *Deploy → Manage deployments → Edit → New version*.
6. In the site: **ID Card Template** page → paste the Google Slides template link, set the validity date, check the hostel/program lists.

## 3. How the workflow runs

| Step | What happens |
|---|---|
| Upload Students | Reads Name, Enrollment No., Password; creates bcrypt-hashed accounts; rejects duplicates/invalid rows with reasons. |
| Student form | One submission per student; photo/signature are validated, re-encoded and stored; they are also uploaded to your Drive folder. |
| Excel | Exact headers/order of your sheet; `DOB`/`Validity` as real dates, enrollment/phones as text, photo/signature as `https://drive.google.com/open?id=…` links. |
| Generate | Images → Drive, data → a new Google Sheet, then the Apps Script runs in batches of 25 students (to stay inside Apps Script's 6-minute limit), exports a PDF, and the site downloads it for you. |

If automatic generation is not set up, download the Excel, import it into a Google Sheet and run `generateIDCards()` exactly as before.

## 4. Changes made to the Apps Script
Card logic (placeholders, photo/signature placement, date format) is unchanged. Fixed/added:
1. **Stray slides:** the copied presentation kept the template's own slides with unfilled `{{…}}`; they are now removed.
2. **PDF export** added (previously only a Slides URL was logged).
3. Runs in **batches** via a Web App entry point (`doPost`), protected by a secret; `generateIDCards()` still works from the Sheet.
4. Values are converted to text before replacement, so numbers or blank cells cannot break a run.
5. Duplicated slides are always removed from the template, even if a student fails midway.
6. Photo/signature problems are **reported to the website** (per student) instead of only being logged.

## 5. Deploy online (one URL for students)
Any host that runs Docker works (Render, Railway, Fly.io, a college VM).
- Set the environment variables from `.env.example` on the host (`DATABASE_URL` from the host's PostgreSQL).
- Persist `/data` (photos, signatures, PDFs) on a volume and back it up with the database.
- Serve over **HTTPS** (hosts above do this automatically; on a VM put Nginx/Caddy in front).
- Keep `SECRET_KEY` long and private. If the admin password is lost, set a new `ADMIN_PASSWORD` and restart.

## Security notes
Passwords are bcrypt hashed; JWT sessions (8 h); role checks on every admin/student route; login attempts are rate-limited;
uploads are size-limited, type-checked and re-encoded; spreadsheet cells can never become formulas; images are only served to the admin.
