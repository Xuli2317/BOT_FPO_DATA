import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

creds_info = json.loads(SERVICE_ACCOUNT_JSON)

creds = service_account.Credentials.from_service_account_info(
    creds_info,
    scopes=["https://www.googleapis.com/auth/drive"]
)

drive = build("drive", "v3", credentials=creds)


def upload_file(local_path, drive_name=None):
    drive_name = drive_name or os.path.basename(local_path)

    file_metadata = {
        "name": drive_name,
        "parents": [FOLDER_ID]
    }

    media = MediaFileUpload(local_path, resumable=True)

    result = drive.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    print(f"Uploaded {drive_name}: {result['id']}")


for root, dirs, files in os.walk("SENTIMENT_INDEX"):
    for filename in files:
        local_path = os.path.join(root, filename)
        upload_file(local_path)
