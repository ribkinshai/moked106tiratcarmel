import random
import pandas as pd
from typing import List, Dict

DAYS_ORDER   = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
SHIFTS       = ["בוקר", "ערב", "לילה"]
NIGHT_LOVERS = {"לב", "איתי", "גיא", "אלינור"}
MORNING_PREF = {"שרית", "רונית", "שני"}

SHIFT_HOURS = {
    "בוקר": "07:00-15:00",
    "ערב":  "15:00-23:00",
    "לילה": "23:00-07:00",
}

# כמה נציגים נדרשים לכל משמרת לפי יום
REQUIRED_PER_SHIFT = {
    "ראשון":  {"בוקר": 3, "ערב": 2, "לילה": 2},
    "שני":    {"בוקר": 3, "ערב": 2, "לילה": 2},
    "שלישי":  {"בוקר": 3, "ערב": 2, "לילה": 2},
    "רביעי":  {"בוקר": 3, "ערב": 2, "לילה": 2},
    "חמישי":  {"בוקר": 3, "ערב": 2, "לילה": 2},
    "שישי":   {"בוקר": 2, "ערב": 2, "לילה": 2},
    "שבת":    {"בוקר": 2, "ערב": 2, "לילה": 2},
}


def generate_schedule(agents: List[Dict], days: List[str]) -> pd.DataFrame:
    random.seed(42)

    names  = [a["name"]  for a in agents]
    totals = {a["name"]: a["total"] for a in agents}
    prefs  = {a["name"]: a["pref"]  for a in agents}

    schedule: Dict[str, Dict[str, str]] = {n: {d: "—" for d in DAYS_ORDER} for n in names}
    assigned_count: Dict[str, int] = {n: 0 for n in names}

    priority_days = ["שישי", "שבת"] + ["ראשון", "שני", "שלישי", "רביעי", "חמישי"]

    def can_assign(name: str, day: str, shift: str) -> bool:
        if assigned_count[name] >= totals[name]:
            return False
        if schedule[name][day] != "—":
            return False
        day_idx = DAYS_ORDER.index(day)
        if shift == "בוקר" and day_idx > 0:
            prev_day = DAYS_ORDER[day_idx - 1]
            if schedule[name][prev_day] == "לילה":
                return False
        return True

    def count_shift_type(name: str, shift_type: str) -> int:
        return sum(1 for d in DAYS_ORDER if schedule[name][d] == shift_type)

    def preferred_shifts(name: str) -> List[str]:
        pref = prefs[name]
        if pref == "לילה" or name in NIGHT_LOVERS:
            return ["לילה", "ערב", "בוקר"]
        elif pref == "בוקר/ערב" or name in MORNING_PREF:
            return ["בוקר", "ערב", "לילה"]
        else:
            return ["בוקר", "ערב", "לילה"]

    def assign(name: str, day: str, shift: str):
        schedule[name][day] = shift
        assigned_count[name] += 1

    # שלב 1 – מילוי לפי עדיפויות
    for day in priority_days:
        for shift in SHIFTS:
            required = REQUIRED_PER_SHIFT[day][shift]

            if shift == "לילה":
                ordered = (
                    [n for n in names if (n in NIGHT_LOVERS or prefs[n] == "לילה")]
                    + [n for n in names if n not in NIGHT_LOVERS and prefs[n] != "לילה"]
                )
            elif shift in ("בוקר", "ערב"):
                ordered = (
                    [n for n in names if (n in MORNING_PREF or prefs[n] == "בוקר/ערב")]
                    + [n for n in names if n not in MORNING_PREF and prefs[n] != "בוקר/ערב"]
                )
            else:
                ordered = list(names)

            assigned_this_shift = 0
            for name in ordered:
                if assigned_this_shift >= required:
                    break
                if can_assign(name, day, shift):
                    if count_shift_type(name, shift) < 4:
                        assign(name, day, shift)
                        assigned_this_shift += 1

    # שלב 2 – השלמה לפי העדפות
    for name in names:
        if assigned_count[name] >= totals[name]:
            continue
        for day in DAYS_ORDER:
            if assigned_count[name] >= totals[name]:
                break
            if schedule[name][day] != "—":
                continue
            for shift in preferred_shifts(name):
                if can_assign(name, day, shift):
                    assign(name, day, shift)
                    break

    # שלב 3 – השלמה שנייה
    for name in names:
        if assigned_count[name] >= totals[name]:
            continue
        for day in DAYS_ORDER:
            if assigned_count[name] >= totals[name]:
                break
            if schedule[name][day] != "—":
                continue
            for shift in SHIFTS:
                if can_assign(name, day, shift):
                    assign(name, day, shift)
                    break

    # בניית DataFrame לפי נציגים (לשימוש פנימי)
    rows = []
    for name in names:
        row = {"שם": name}
        for day in DAYS_ORDER:
            row[day] = schedule[name][day]
        row["סה״כ"] = assigned_count[name]
        rows.append(row)

    return pd.DataFrame(rows)


def build_shift_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    בונה טבלה לפי משמרות:
    שורות = (יום, משמרת+שעות)
    עמודות = נציג 1, נציג 2, ...
    """
    rows = []
    for day in DAYS_ORDER:
        for shift in SHIFTS:
            hours = SHIFT_HOURS[shift]
            agents_in_shift = df[df[day] == shift]["שם"].tolist()
            row = {
                "יום": day,
                "משמרת": f"{shift}\n{hours}",
            }
            for i, agent in enumerate(agents_in_shift):
                row[f"נציג {i+1}"] = agent
            rows.append(row)
    return pd.DataFrame(rows)
