import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT_LOCAL = "SENTIMENT_INDEX"
FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
TOKEN_JSON = os.getenv("GOOGLE_OAUTH_TOKEN_JSON")

if not FOLDER_ID:
    raise ValueError("Missing GOOGLE_DRIVE_FOLDER_ID")

if not TOKEN_JSON:
    raise ValueError("Missing GOOGLE_OAUTH_TOKEN_JSON")

creds = Credentials.from_authorized_user_info(
    json.loads(TOKEN_JSON),
    scopes=["https://www.googleapis.com/auth/drive"]
)

drive = build("drive", "v3", credentials=creds)

folder_cache = {}


def esc(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")


def find_folder_in_parent(name, parent_id):
    query = (
        f"name = '{esc(name)}' and "
        f"mimeType = 'application/vnd.google-apps.folder' and "
        f"'{parent_id}' in parents and "
        f"trashed = false"
    )

    res = drive.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name, parents)"
    ).execute()

    files = res.get("files", [])

    if len(files) > 1:
        print(f"WARNING: duplicate folder name found: {name}, using first one")

    return files[0]["id"] if files else None


def get_or_create_folder(name, parent_id):
    key = (parent_id, name)

    if key in folder_cache:
        return folder_cache[key]

    folder_id = find_folder_in_parent(name, parent_id)

    if folder_id:
        print(f"Using existing folder: {name}")
        folder_cache[key] = folder_id
        return folder_id

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


def find_file_in_parent(filename, parent_id):
    query = (
        f"name = '{esc(filename)}' and "
        f"'{parent_id}' in parents and "
        f"mimeType != 'application/vnd.google-apps.folder' and "
        f"trashed = false"
    )

    res = drive.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name, parents)"
    ).execute()

    files = res.get("files", [])

    if len(files) > 1:
        print(f"WARNING: duplicate file name found: {filename}, updating first one")

    return files[0]["id"] if files else None


def upload_or_update_file(local_path):
    filename = os.path.basename(local_path)
    parent_id = get_drive_folder_for_path(os.path.dirname(local_path))

    media = MediaFileUpload(local_path, resumable=True)
    file_id = find_file_in_parent(filename, parent_id)

    if file_id:
        result = drive.files().update(
            fileId=file_id,
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
