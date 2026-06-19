import json
import base64
import requests
import pandas as pd
import streamlit as st
from datetime import datetime

ARCHIVE_PATH = "archive.json"


def _get_token_and_repo():
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo  = st.secrets["GITHUB_REPO"]
        return token, repo
    except Exception:
        return None, None


def _github_get_file(path):
    """מחזיר (content_dict, sha) או (None, None) אם לא קיים"""
    token, repo = _get_token_and_repo()
    if not token:
        return None, None
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content), data["sha"]
    return None, None


def _github_save_file(path, content_dict, sha=None):
    token, repo = _get_token_and_repo()
    if not token:
        return False
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    content_json = json.dumps(content_dict, ensure_ascii=False, indent=2)
    encoded = base64.b64encode(content_json.encode("utf-8")).decode("utf-8")
    payload = {
        "message": f"Update archive {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "content": encoded,
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(url, headers=headers, json=payload)
    return r.status_code in (200, 201)


def load_archive():
    archive, _ = _github_get_file(ARCHIVE_PATH)
    return archive if archive else []


def save_to_archive(df, week_label, notes=""):
    archive, sha = _github_get_file(ARCHIVE_PATH)
    if archive is None:
        archive = []
    entry = {
        "week":     week_label,
        "date":     datetime.now().strftime("%d/%m/%Y %H:%M"),
        "notes":    notes,
        "schedule": df.to_dict(orient="records"),
    }
    archive = [a for a in archive if a["week"] != week_label]
    archive.append(entry)
    archive.sort(key=lambda x: x["week"], reverse=True)
    _github_save_file(ARCHIVE_PATH, archive, sha)


def delete_from_archive(week_label):
    archive, sha = _github_get_file(ARCHIVE_PATH)
    if archive is None:
        return
    archive = [a for a in archive if a["week"] != week_label]
    _github_save_file(ARCHIVE_PATH, archive, sha)


def archive_to_df(entry):
    return pd.DataFrame(entry["schedule"])
