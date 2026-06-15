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


def get_or_create_folder(name, parent_id):
    query = (
        f"name='{name}' and "
        f"mimeType='application/vnd.google-apps.folder' and "
        f"'{parent_id}' in parents and trashed=false"
    )

    res = drive.files().list(
        q=query,
        fields="files(id, name)"
    ).execute()

    files = res.get("files", [])

    if files:
        return files[0]["id"]

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }

    folder = drive.files().create(
        body=metadata,
        fields="id"
    ).execute()

    return folder["id"]


def get_drive_folder_for_path(local_dir):
    rel_path = os.path.relpath(local_dir, ROOT_LOCAL)

    current_parent = FOLDER_ID

    if rel_path == ".":
        return current_parent

    for part in rel_path.split(os.sep):
        current_parent = get_or_create_folder(part, current_parent)

    return current_parent


def upload_file(local_path):
    filename = os.path.basename(local_path)
    parent_id = get_drive_folder_for_path(os.path.dirname(local_path))

    media = MediaFileUpload(local_path, resumable=True)

    metadata = {
        "name": filename,
        "parents": [parent_id]
    }

    result = drive.files().create(
        body=metadata,
        media_body=media,
        fields="id"
    ).execute()

    print(f"Uploaded {local_path}: {result['id']}")


for root, dirs, files in os.walk(ROOT_LOCAL):
    for filename in files:
        if filename.startswith("."):
            continue

        local_path = os.path.join(root, filename)
        upload_file(local_path)
