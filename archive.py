import json
import os
from datetime import datetime
from typing import Dict, List
import pandas as pd

ARCHIVE_FILE = "archive.json"


def load_archive() -> List[Dict]:
    if not os.path.exists(ARCHIVE_FILE):
        return []
    with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_to_archive(df: pd.DataFrame, week_label: str, notes: str = ""):
    archive = load_archive()
    entry = {
        "week":      week_label,
        "date":      datetime.now().strftime("%d/%m/%Y %H:%M"),
        "notes":     notes,
        "schedule":  df.to_dict(orient="records"),
    }
    # החלף אם כבר קיים אותו שבוע
    archive = [a for a in archive if a["week"] != week_label]
    archive.append(entry)
    archive.sort(key=lambda x: x["week"], reverse=True)
    with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=2)


def delete_from_archive(week_label: str):
    archive = load_archive()
    archive = [a for a in archive if a["week"] != week_label]
    with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=2)


def archive_to_df(entry: Dict) -> pd.DataFrame:
    return pd.DataFrame(entry["schedule"])