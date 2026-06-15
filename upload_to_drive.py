import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT_LOCAL = "SENTIMENT_INDEX"
FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
TOKEN_JSON = os.getenv("GOOGLE_OAUTH_TOKEN_JSON")

creds = Credentials.from_authorized_user_info(
    json.loads(TOKEN_JSON),
    scopes=["https://www.googleapis.com/auth/drive"]
)

drive = build("drive", "v3", credentials=creds)

folder_cache = {}


def esc(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")


def get_or_create_folder(name, parent_id):
    key = (parent_id, name)

    if key in folder_cache:
        return folder_cache[key]

    query = (
        f"name = '{esc(name)}' and "
        f"mimeType = 'application/vnd.google-apps.folder' and "
        f"trashed = false"
    )

    res = drive.files().list(
        q=query,
        spaces="drive",
        corpora="user",
        fields="files(id, name, parents)"
    ).execute()

    for f in res.get("files", []):
        if parent_id in f.get("parents", []):
            folder_cache[key] = f["id"]
            print(f"Using existing folder: {name}")
            return f["id"]

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }

    folder = drive.files().create(
        body=metadata,
        fields="id"
    ).execute()

    folder_cache[key] = folder["id"]
    print(f"Created folder: {name}")

    return folder["id"]


def get_drive_folder_for_path(local_dir):
    rel_path = os.path.relpath(local_dir, ROOT_LOCAL)

    current_parent = FOLDER_ID

    if rel_path == ".":
        return current_parent

    for part in rel_path.split(os.sep):
        current_parent = get_or_create_folder(part, current_parent)

    return current_parent


def find_existing_file(filename, parent_id):
    query = (
        f"name = '{esc(filename)}' and "
        f"'{parent_id}' in parents and "
        f"mimeType != 'application/vnd.google-apps.folder' and "
        f"trashed = false"
    )

    res = drive.files().list(
        q=query,
        spaces="drive",
        corpora="user",
        fields="files(id, name)"
    ).execute()

    files = res.get("files", [])
    return files[0]["id"] if files else None


def upload_or_update_file(local_path):
    filename = os.path.basename(local_path)
    parent_id = get_drive_folder_for_path(os.path.dirname(local_path))

    media = MediaFileUpload(local_path, resumable=True)

    existing_file_id = find_existing_file(filename, parent_id)

    if existing_file_id:
        result = drive.files().update(
            fileId=existing_file_id,
            media_body=media,
            fields="id"
        ).execute()

        print(f"Updated: {local_path} -> {result['id']}")
    else:
        metadata = {
            "name": filename,
            "parents": [parent_id]
        }

        result = drive.files().create(
            body=metadata,
            media_body=media,
            fields="id"
        ).execute()

        print(f"Uploaded: {local_path} -> {result['id']}")


for root, dirs, files in os.walk(ROOT_LOCAL):
    for filename in files:
        if filename.startswith("."):
            continue

        local_path = os.path.join(root, filename)
        upload_or_update_file(local_path)
