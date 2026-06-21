import json
import base64
import requests
import pandas as pd
import streamlit as st

CURRENT_PATH = "current_schedule.json"


def _get_token_and_repo():
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo  = st.secrets["GITHUB_REPO"]
        return token, repo
    except Exception:
        return None, None


def _github_get_file(path):
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
        "message": "Update current schedule",
        "content": encoded,
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(url, headers=headers, json=payload)
    return r.status_code in (200, 201)


def save_current(df, twelve_hour, watcher, cell_notes, week_label, week_notes):
    data = {
        "schedule":    df.to_dict(orient="records") if df is not None else None,
        "twelve_hour": twelve_hour,
        "watcher":     watcher,
        "cell_notes":  cell_notes,
        "week_label":  week_label,
        "week_notes":  week_notes,
    }
    _, sha = _github_get_file(CURRENT_PATH)
    _github_save_file(CURRENT_PATH, data, sha)


def load_current():
    data, _ = _github_get_file(CURRENT_PATH)
    if data is None:
        return None
    if data.get("schedule"):
        data["schedule"] = pd.DataFrame(data["schedule"])
    return data
