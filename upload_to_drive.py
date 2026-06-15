import os
import json
import hashlib
import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT_LOCAL = "SENTIMENT_INDEX"
FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
TOKEN_JSON = os.getenv("GOOGLE_OAUTH_TOKEN_JSON")

UPLOAD_CHECKPOINT_FILE = os.path.join(
    ROOT_LOCAL, "CODE", "checkpoint", "upload_checkpoint.parquet"
)

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


def get_md5(path):
    h = hashlib.md5()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)

    return h.hexdigest()


def load_checkpoint():
    if os.path.exists(UPLOAD_CHECKPOINT_FILE):
        return pd.read_parquet(UPLOAD_CHECKPOINT_FILE)

    return pd.DataFrame(columns=["path", "md5"])


def save_checkpoint(df):
    os.makedirs(os.path.dirname(UPLOAD_CHECKPOINT_FILE), exist_ok=True)
    df.to_parquet(UPLOAD_CHECKPOINT_FILE, index=False)
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
        print(f"WARNING duplicate folder: {name}, using first one")

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

    folder = drive.files().create(
        body={
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id]
        },
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
        print(f"WARNING duplicate file: {filename}, updating first one")

    return files[0]["id"] if files else None

def upload_or_update_file(local_path):
    filename = os.path.basename(local_path)
    parent_id = get_drive_folder_for_path(os.path.dirname(local_path))
    file_id = find_file_in_parent(filename, parent_id)

    media = MediaFileUpload(local_path, resumable=True)

    if file_id:
        result = drive.files().update(
            fileId=file_id,
            media_body=media,
            fields="id"
        ).execute()
        print(f"Updated: {local_path} -> {result['id']}")
    else:
        result = drive.files().create(
            body={
                "name": filename,
                "parents": [parent_id]
            },
            media_body=media,
            fields="id"
        ).execute()
        print(f"Uploaded: {local_path} -> {result['id']}")


df_upload = load_checkpoint()

for root, dirs, files in os.walk(ROOT_LOCAL):
    for filename in files:
        if filename.startswith("."):
            continue

        local_path = os.path.join(root, filename)

        if local_path == UPLOAD_CHECKPOINT_FILE:
            continue

        file_md5 = get_md5(local_path)

        old = df_upload[df_upload["path"] == local_path]

        if not old.empty and old.iloc[0]["md5"] == file_md5:
            print(f"Skip unchanged: {local_path}")
            continue

        upload_or_update_file(local_path)

        df_upload = df_upload[df_upload["path"] != local_path]

        df_upload = pd.concat(
            [
                df_upload,
                pd.DataFrame([{
                    "path": local_path,
                    "md5": file_md5
                }])
            ],
            ignore_index=True
        )

        save_checkpoint(df_upload)
