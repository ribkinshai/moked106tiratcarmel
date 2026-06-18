import pandas as pd
from typing import List, Dict

DAYS_ORDER = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
SHIFTS     = ["בוקר", "ערב", "לילה"]

SHIFT_HOURS = {
    "בוקר": "07:00-15:00",
    "ערב":  "15:00-23:00",
    "לילה": "23:00-07:00",
}

REQUIRED_PER_SHIFT = {
    "ראשון":  {"בוקר": 3, "ערב": 2, "לילה": 2},
    "שני":    {"בוקר": 3, "ערב": 2, "לילה": 2},
    "שלישי":  {"בוקר": 3, "ערב": 2, "לילה": 2},
    "רביעי":  {"בוקר": 3, "ערב": 2, "לילה": 2},
    "חמישי":  {"בוקר": 3, "ערב": 2, "לילה": 2},
    "שישי":   {"בוקר": 2, "ערב": 2, "לילה": 2},
    "שבת":    {"בוקר": 2, "ערב": 2, "לילה": 2},
}

# משמרות קבועות: {שם: {יום: משמרת}}
FIXED_SHIFTS = {
    "שרית": {"ראשון": "בוקר", "שני": "בוקר", "חמישי": "בוקר"},
    "ריקי":  {"ראשון": "בוקר", "שני": "בוקר", "חמישי": "בוקר"},
    "אדיר": {"ראשון": "בוקר", "חמישי": "בוקר"},
}

# אילוצים אישיים: {שם: [(יום, משמרת אסורה)]}
FORBIDDEN = {
    "טלי":  [("שבת", "לילה"), ("ראשון", "בוקר")],
    "ריקי": [("שבת", "בוקר"), ("שבת", "ערב"), ("שבת", "לילה"),
              ("שלישי", "בוקר"), ("שלישי", "ערב"), ("שלישי", "לילה"),
              ("רביעי", "בוקר"), ("רביעי", "ערב"), ("רביעי", "לילה"),
              ("שישי", "בוקר"), ("שישי", "ערב"), ("שישי", "לילה")],
}

NIGHT_LOVERS = {"לב", "איתי", "גיא", "אלינור"}
DIVERSE_AGENTS = {"שני", "רונית"}  # פיזור מגוון


def generate_schedule(agents: List[Dict], days: List[str], is_fourth_saturday: bool = True) -> pd.DataFrame:
    names  = [a["name"]  for a in agents]
    totals = {a["name"]: a["total"] for a in agents}

    schedule: Dict[str, Dict[str, str]] = {n: {d: "—" for d in DAYS_ORDER} for n in names}
    assigned_count: Dict[str, int]      = {n: 0 for n in names}
    shift_type_count: Dict[str, Dict[str, int]] = {
        n: {"בוקר": 0, "ערב": 0, "לילה": 0} for n in names
    }

    # אם לא שבת רביעית – ריקי לא עובדת שבת (כבר בFORBIDDEN)
    # אם כן שבת רביעית – מוסיפים משמרת שבת לריקי (מכסה עולה ל-4)
    if is_fourth_saturday:
        totals["ריקי"] = 4
        # מסירים את איסור שבת מריקי
        FORBIDDEN["ריקי"] = [d for d in FORBIDDEN.get("ריקי", []) 
                              if d[0] != "שבת"]

    def is_forbidden(name: str, day: str, shift: str) -> bool:
        for (fd, fs) in FORBIDDEN.get(name, []):
            if fd == day and fs == shift:
                return True
        return False

    def can_assign(name: str, day: str, shift: str) -> bool:
        if assigned_count[name] >= totals[name]:
            return False
        if schedule[name][day] != "—":
            return False
        if is_forbidden(name, day, shift):
            return False
        # אסור בוקר אחרי לילה
        day_idx = DAYS_ORDER.index(day)
        if shift == "בוקר" and day_idx > 0:
            prev_day = DAYS_ORDER[day_idx - 1]
            if schedule[name][prev_day] == "לילה":
                return False
        return True

    def assign(name: str, day: str, shift: str):
        schedule[name][day] = shift
        assigned_count[name] += 1
        shift_type_count[name][shift] += 1

    def diversity_score(name: str, shift: str) -> int:
        """ציון פיזור – מעדיף משמרות שנציג עשה פחות"""
        return shift_type_count[name][shift]

    # ── שלב 1: שיבוץ משמרות קבועות ──
    for name, fixed in FIXED_SHIFTS.items():
        if name not in names:
            continue
        for day, shift in fixed.items():
            if can_assign(name, day, shift):
                assign(name, day, shift)

    # ── שלב 2: מילוי לפי דרישות, עדיפויות ופריסה ──
    priority_days = ["שישי", "שבת"] + ["ראשון", "שני", "שלישי", "רביעי", "חמישי"]

    for day in priority_days:
        for shift in SHIFTS:
            required = REQUIRED_PER_SHIFT[day][shift]
            already  = sum(1 for n in names if schedule[n][day] == shift)
            needed   = required - already
            if needed <= 0:
                continue

            # בניית רשימת עדיפויות
            if shift == "לילה":
                primary   = [n for n in names if n in NIGHT_LOVERS]
                secondary = [n for n in names if n not in NIGHT_LOVERS]
            elif shift == "בוקר":
                primary   = [n for n in names if n not in NIGHT_LOVERS and n not in DIVERSE_AGENTS]
                secondary = sorted(DIVERSE_AGENTS & set(names),
                                   key=lambda n: diversity_score(n, shift))
                tertiary  = [n for n in names if n in NIGHT_LOVERS]
                secondary = secondary + tertiary
            else:  # ערב
                primary   = [n for n in names if n not in NIGHT_LOVERS]
                secondary = [n for n in names if n in NIGHT_LOVERS]

            # נציגי פיזור – ממוינים לפי מי עשה פחות מהמשמרת הזו
            def sort_key(n):
                base = 0 if n in primary else 1
                div  = diversity_score(n, shift) if n in DIVERSE_AGENTS else 0
                return (base, div, assigned_count[n])

            ordered = sorted(names, key=sort_key)

            filled = 0
            for name in ordered:
                if filled >= needed:
                    break
                if can_assign(name, day, shift):
                    # פיזור: לא יותר מ-3 מאותו סוג (אלא אם אין ברירה)
                    if shift_type_count[name][shift] < 3:
                        assign(name, day, shift)
                        filled += 1

            # אם עדיין חסרים – נרגיש את הגבלת הפיזור
            if filled < needed:
                for name in ordered:
                    if filled >= needed:
                        break
                    if can_assign(name, day, shift):
                        assign(name, day, shift)
                        filled += 1

    # ── שלב 3: השלמה למכסה ──
    for name in names:
        if assigned_count[name] >= totals[name]:
            continue
        # ממיין ימים לפי איזון פיזור
        for day in DAYS_ORDER:
            if assigned_count[name] >= totals[name]:
                break
            if schedule[name][day] != "—":
                continue
            # סדר משמרות לפי פיזור
            if name in NIGHT_LOVERS:
                shift_order = sorted(SHIFTS, key=lambda s: shift_type_count[name][s])
                shift_order = sorted(shift_order, key=lambda s: 0 if s == "לילה" else 1)
            elif name in DIVERSE_AGENTS:
                shift_order = sorted(SHIFTS, key=lambda s: shift_type_count[name][s])
            else:
                shift_order = sorted(SHIFTS, key=lambda s: shift_type_count[name][s])

            for shift in shift_order:
                if can_assign(name, day, shift):
                    assign(name, day, shift)
                    break

    # ── בניית DataFrame ──
    rows = []
    for name in names:
        row = {"שם": name}
        for day in DAYS_ORDER:
            row[day] = schedule[name][day]
        row["סה״כ"] = assigned_count[name]
        rows.append(row)

    return pd.DataFrame(rows)
