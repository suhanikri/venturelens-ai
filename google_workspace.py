"""Gmail and Google Drive for VentureLens (same pattern as smart-support-agent)."""
import base64
import io
import json
import os
from email.message import EmailMessage

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/drive.file",
]
TOKEN_FILE = "token.json"


def configured():
    return bool(os.getenv("GOOGLE_OAUTH_TOKEN_JSON") or os.path.exists(TOKEN_FILE))


def get_credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    raw = os.getenv("GOOGLE_OAUTH_TOKEN_JSON")
    info = json.loads(raw) if raw else json.load(open(TOKEN_FILE))
    creds = Credentials.from_authorized_user_info(info, SCOPES)
    if not creds.valid:
        creds.refresh(Request())
    return creds


def _service(name, version):
    from googleapiclient.discovery import build

    return build(name, version, credentials=get_credentials(), cache_discovery=False)


def send_report_email(to, subject, body, attachments=None):
    """attachments: list of (filename, pdf_bytes).
    EMAIL_MODE=draft (default) saves a Gmail draft; EMAIL_MODE=send sends it."""
    mode = os.getenv("EMAIL_MODE", "draft").lower()
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    for filename, data in attachments or []:
        msg.add_attachment(data, maintype="application", subtype="pdf", filename=filename)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    gmail = _service("gmail", "v1")
    if mode == "send":
        sent = gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
        return {"mode": "sent", "id": sent["id"]}
    draft = gmail.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
    return {"mode": "draft", "id": draft["id"]}


def _folder(drive, name, parent=None):
    safe = name.replace("\\", "\\\\").replace("'", "\\'")
    q = f"name = '{safe}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent:
        q += f" and '{parent}' in parents"
    found = drive.files().list(q=q, fields="files(id)", pageSize=1).execute().get("files", [])
    if found:
        return found[0]["id"]
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent:
        meta["parents"] = [parent]
    return drive.files().create(body=meta, fields="id").execute()["id"]


def save_to_drive(application_id, startup, files):
    """files: list of (filename, bytes, mime_type). Returns the folder link."""
    from googleapiclient.http import MediaIoBaseUpload

    drive = _service("drive", "v3")
    root = _folder(drive, os.getenv("DRIVE_FOLDER_NAME", "VentureLens"))
    folder = _folder(drive, f"{startup} - {application_id}", root)
    for filename, data, mime in files:
        media = MediaIoBaseUpload(io.BytesIO(data), mimetype=mime)
        drive.files().create(body={"name": filename, "parents": [folder]},
                             media_body=media, fields="id").execute()
    return f"https://drive.google.com/drive/folders/{folder}"
