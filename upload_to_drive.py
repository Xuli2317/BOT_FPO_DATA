{
  "nbformat": 4,
  "nbformat_minor": 0,
  "metadata": {
    "colab": {
      "provenance": [],
      "authorship_tag": "ABX9TyNIcS5pufg9MEyoyV5taUge",
      "include_colab_link": true
    },
    "kernelspec": {
      "name": "python3",
      "display_name": "Python 3"
    },
    "language_info": {
      "name": "python"
    }
  },
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "view-in-github",
        "colab_type": "text"
      },
      "source": [
        "<a href=\"https://colab.research.google.com/github/Xuli2317/BOT_FPO_DATA/blob/main/upload_to_drive.py\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {
        "id": "9x_yVc4y44XK"
      },
      "outputs": [],
      "source": [
        "import os\n",
        "import json\n",
        "import hashlib\n",
        "import pandas as pd\n",
        "from google.oauth2.credentials import Credentials\n",
        "from googleapiclient.discovery import build\n",
        "from googleapiclient.http import MediaFileUpload\n",
        "\n",
        "ROOT_LOCAL = \"SENTIMENT_INDEX\"\n",
        "FOLDER_ID = os.getenv(\"GOOGLE_DRIVE_FOLDER_ID\")\n",
        "TOKEN_JSON = os.getenv(\"GOOGLE_OAUTH_TOKEN_JSON\")\n",
        "\n",
        "UPLOAD_CHECKPOINT_FILE = os.path.join(\n",
        "    ROOT_LOCAL, \"CODE\", \"checkpoint\", \"upload_checkpoint.parquet\"\n",
        ")\n",
        "\n",
        "if not FOLDER_ID:\n",
        "    raise ValueError(\"Missing GOOGLE_DRIVE_FOLDER_ID\")\n",
        "\n",
        "if not TOKEN_JSON:\n",
        "    raise ValueError(\"Missing GOOGLE_OAUTH_TOKEN_JSON\")\n",
        "\n",
        "creds = Credentials.from_authorized_user_info(\n",
        "    json.loads(TOKEN_JSON),\n",
        "    scopes=[\"https://www.googleapis.com/auth/drive\"]\n",
        ")\n",
        "\n",
        "drive = build(\"drive\", \"v3\", credentials=creds)\n",
        "\n",
        "folder_cache = {}"
      ]
    },
    {
      "cell_type": "code",
      "source": [
        "def esc(s):\n",
        "    return s.replace(\"\\\\\", \"\\\\\\\\\").replace(\"'\", \"\\\\'\")\n",
        "\n",
        "\n",
        "def get_md5(path):\n",
        "    h = hashlib.md5()\n",
        "\n",
        "    with open(path, \"rb\") as f:\n",
        "        for chunk in iter(lambda: f.read(8192), b\"\"):\n",
        "            h.update(chunk)\n",
        "\n",
        "    return h.hexdigest()\n",
        "\n",
        "\n",
        "def load_checkpoint():\n",
        "    if os.path.exists(UPLOAD_CHECKPOINT_FILE):\n",
        "        return pd.read_parquet(UPLOAD_CHECKPOINT_FILE)\n",
        "\n",
        "    return pd.DataFrame(columns=[\"path\", \"md5\"])\n",
        "\n",
        "\n",
        "def save_checkpoint(df):\n",
        "    os.makedirs(os.path.dirname(UPLOAD_CHECKPOINT_FILE), exist_ok=True)\n",
        "    df.to_parquet(UPLOAD_CHECKPOINT_FILE, index=False)\n"
      ],
      "metadata": {
        "id": "5nDLhOxvAM7q"
      },
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "source": [
        "def find_folder_in_parent(name, parent_id):\n",
        "    query = (\n",
        "        f\"name = '{esc(name)}' and \"\n",
        "        f\"mimeType = 'application/vnd.google-apps.folder' and \"\n",
        "        f\"'{parent_id}' in parents and \"\n",
        "        f\"trashed = false\"\n",
        "    )\n",
        "\n",
        "    res = drive.files().list(\n",
        "        q=query,\n",
        "        spaces=\"drive\",\n",
        "        fields=\"files(id, name, parents)\"\n",
        "    ).execute()\n",
        "\n",
        "    files = res.get(\"files\", [])\n",
        "\n",
        "    if len(files) > 1:\n",
        "        print(f\"WARNING duplicate folder: {name}, using first one\")\n",
        "\n",
        "    return files[0][\"id\"] if files else None"
      ],
      "metadata": {
        "id": "t_Ly6SIZAQnx"
      },
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "source": [
        "def get_or_create_folder(name, parent_id):\n",
        "    key = (parent_id, name)\n",
        "\n",
        "    if key in folder_cache:\n",
        "        return folder_cache[key]\n",
        "\n",
        "    folder_id = find_folder_in_parent(name, parent_id)\n",
        "\n",
        "    if folder_id:\n",
        "        print(f\"Using existing folder: {name}\")\n",
        "        folder_cache[key] = folder_id\n",
        "        return folder_id\n",
        "\n",
        "    folder = drive.files().create(\n",
        "        body={\n",
        "            \"name\": name,\n",
        "            \"mimeType\": \"application/vnd.google-apps.folder\",\n",
        "            \"parents\": [parent_id]\n",
        "        },\n",
        "        fields=\"id\"\n",
        "    ).execute()\n",
        "\n",
        "    folder_cache[key] = folder[\"id\"]\n",
        "    print(f\"Created folder: {name}\")\n",
        "\n",
        "    return folder[\"id\"]"
      ],
      "metadata": {
        "id": "NuSv-hqcAf10"
      },
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "source": [
        "def get_drive_folder_for_path(local_dir):\n",
        "    rel_path = os.path.relpath(local_dir, ROOT_LOCAL)\n",
        "    current_parent = FOLDER_ID\n",
        "\n",
        "    if rel_path == \".\":\n",
        "        return current_parent\n",
        "\n",
        "    for part in rel_path.split(os.sep):\n",
        "        current_parent = get_or_create_folder(part, current_parent)\n",
        "\n",
        "    return current_parent\n",
        "\n",
        "\n"
      ],
      "metadata": {
        "id": "N-1vCBv_ATj7"
      },
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "source": [
        "def find_file_in_parent(filename, parent_id):\n",
        "    query = (\n",
        "        f\"name = '{esc(filename)}' and \"\n",
        "        f\"'{parent_id}' in parents and \"\n",
        "        f\"mimeType != 'application/vnd.google-apps.folder' and \"\n",
        "        f\"trashed = false\"\n",
        "    )\n",
        "\n",
        "    res = drive.files().list(\n",
        "        q=query,\n",
        "        spaces=\"drive\",\n",
        "        fields=\"files(id, name, parents)\"\n",
        "    ).execute()\n",
        "\n",
        "    files = res.get(\"files\", [])\n",
        "\n",
        "    if len(files) > 1:\n",
        "        print(f\"WARNING duplicate file: {filename}, updating first one\")\n",
        "\n",
        "    return files[0][\"id\"] if files else None"
      ],
      "metadata": {
        "id": "vLgHsOWLAXTr"
      },
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "source": [
        "def upload_or_update_file(local_path):\n",
        "    filename = os.path.basename(local_path)\n",
        "    parent_id = get_drive_folder_for_path(os.path.dirname(local_path))\n",
        "    file_id = find_file_in_parent(filename, parent_id)\n",
        "\n",
        "    media = MediaFileUpload(local_path, resumable=True)\n",
        "\n",
        "    if file_id:\n",
        "        result = drive.files().update(\n",
        "            fileId=file_id,\n",
        "            media_body=media,\n",
        "            fields=\"id\"\n",
        "        ).execute()\n",
        "        print(f\"Updated: {local_path} -> {result['id']}\")\n",
        "    else:\n",
        "        result = drive.files().create(\n",
        "            body={\n",
        "                \"name\": filename,\n",
        "                \"parents\": [parent_id]\n",
        "            },\n",
        "            media_body=media,\n",
        "            fields=\"id\"\n",
        "        ).execute()\n",
        "        print(f\"Uploaded: {local_path} -> {result['id']}\")\n",
        "\n",
        "\n",
        "df_upload = load_checkpoint()\n",
        "\n",
        "for root, dirs, files in os.walk(ROOT_LOCAL):\n",
        "    for filename in files:\n",
        "        if filename.startswith(\".\"):\n",
        "            continue\n",
        "\n",
        "        local_path = os.path.join(root, filename)\n",
        "\n",
        "        if local_path == UPLOAD_CHECKPOINT_FILE:\n",
        "            continue\n",
        "\n",
        "        file_md5 = get_md5(local_path)\n",
        "\n",
        "        old = df_upload[df_upload[\"path\"] == local_path]\n",
        "\n",
        "        if not old.empty and old.iloc[0][\"md5\"] == file_md5:\n",
        "            print(f\"Skip unchanged: {local_path}\")\n",
        "            continue\n",
        "\n",
        "        upload_or_update_file(local_path)\n",
        "\n",
        "        df_upload = df_upload[df_upload[\"path\"] != local_path]\n",
        "\n",
        "        df_upload = pd.concat(\n",
        "            [\n",
        "                df_upload,\n",
        "                pd.DataFrame([{\n",
        "                    \"path\": local_path,\n",
        "                    \"md5\": file_md5\n",
        "                }])\n",
        "            ],\n",
        "            ignore_index=True\n",
        "        )\n",
        "\n",
        "        save_checkpoint(df_upload)"
      ],
      "metadata": {
        "id": "ohjZV13GAVci"
      },
      "execution_count": null,
      "outputs": []
    }
  ]
}