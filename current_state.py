import json
import os
import pandas as pd

CURRENT_FILE = "current_schedule.json"


def save_current(df, twelve_hour, watcher, cell_notes, week_label, week_notes):
    data = {
        "schedule":    df.to_dict(orient="records") if df is not None else None,
        "twelve_hour": twelve_hour,
        "watcher":     watcher,
        "cell_notes":  cell_notes,
        "week_label":  week_label,
        "week_notes":  week_notes,
    }
    with open(CURRENT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_current():
    if not os.path.exists(CURRENT_FILE):
        return None
    try:
        with open(CURRENT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("schedule"):
            data["schedule"] = pd.DataFrame(data["schedule"])
        return data
    except Exception:
        return None