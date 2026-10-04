from dotenv import load_dotenv

load_dotenv()
import google_workspace as g

drive = g._service("drive", "v3")
folders = drive.files().list(
    q="mimeType='application/vnd.google-apps.folder' and trashed=false",
    fields="files(id,name,parents)", pageSize=50).execute().get("files", [])
print("FOLDERS:")
for f in folders:
    print(" ", f["name"], "| id:", f["id"], "| parent:", f.get("parents"))
files = drive.files().list(
    q="mimeType!='application/vnd.google-apps.folder' and trashed=false",
    fields="files(name,parents)", pageSize=20).execute().get("files", [])
print("FILES:")
for f in files:
    print(" ", f["name"], "| parent:", f.get("parents"))
