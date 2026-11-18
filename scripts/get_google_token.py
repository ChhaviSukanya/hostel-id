"""One-time helper: prints the refresh token for the department Google account.
Usage:  python scripts/get_google_token.py <CLIENT_ID> <CLIENT_SECRET>
Sign in with the SAME Google account that owns the Apps Script and the Drive folder."""
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

cid, secret = sys.argv[1], sys.argv[2]
flow = InstalledAppFlow.from_client_config(
    {"installed": {"client_id": cid, "client_secret": secret,
                   "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                   "token_uri": "https://oauth2.googleapis.com/token",
                   "redirect_uris": ["http://localhost"]}},
    ["https://www.googleapis.com/auth/drive"])
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
print("\nGOOGLE_REFRESH_TOKEN=" + creds.refresh_token)
