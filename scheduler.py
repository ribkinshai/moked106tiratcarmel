import copy
import pandas as pd
from typing import List, Dict

DAYS_ORDER = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
SHIFTS     = ["בוקר", "ערב", "לילה"]

SHIFT_HOURS = {
    "בוקר":    "07:00-15:00",
    "בוקר 12": "07:00-19:00",
    "ערב":     "15:00-23:00",
    "לילה":    "23:00-07:00",
    "לילה 12": "19:00-07:00",
}

REQUIRED_PER_SHIFT = {
    "ראשון":  {"בוקר": 3, "ערב": 2, "לילה": 2},
    "שני":    {"בוקר": 3, "ערב": 2, "לילה": 2},
    "שלישי":  {"בוקר": 3, "ערב": 2, "לילה": 2},
    "רביעי":  {"בוקר": 3, "ערב": 2, "לילה": 2},
    "חמישי":  {"בוקר": 3, "ערב": 2, "לילה": 2},
    "שישי":   {"בוקר": 3, "ערב": 2, "לילה": 2},
    "שבת":    {"בוקר": 2, "ערב": 2, "לילה": 2},
}

# משמרות קבועות – לא נספרות מחדש בשלב 2
FIXED_SHIFTS = {
    "שרית": {"ראשון": "בוקר", "שני": "בוקר", "חמישי": "בוקר"},
    "ריקי": {"ראשון": "בוקר", "שני": "בוקר", "חמישי": "בוקר"},
    "אדיר": {"ראשון": "בוקר", "חמישי": "בוקר"},
    "סימה": {"שני": "ערב", "שלישי": "ערב"},
}

FORBIDDEN_DEFAULT = {
    "טלי": [("שבת", "לילה"), ("ראשון", "בוקר")],
    "ריקי": [
        ("שבת", "בוקר"), ("שבת", "ערב"), ("שבת", "לילה"),
        ("שלישי", "בוקר"), ("שלישי", "ערב"), ("שלישי", "לילה"),
        ("רביעי", "בוקר"), ("רביעי", "ערב"), ("רביעי", "לילה"),
        ("שישי", "בוקר"), ("שישי", "ערב"), ("שישי", "לילה"),
    ],
    "סימה": [
        ("ראשון", "בוקר"), ("ראשון", "ערב"), ("ראשון", "לילה"),
        ("חמישי", "בוקר"), ("חמישי", "ערב"), ("חמישי", "לילה"),
        ("שישי", "בוקר"), ("שישי", "ערב"), ("שישי", "לילה"),
        ("שבת", "בוקר"), ("שבת", "ערב"), ("שבת", "לילה"),
        ("שני", "בוקר"), ("שני", "לילה"),
        ("שלישי", "בוקר"), ("שלישי", "לילה"),
        ("רביעי", "בוקר"), ("רביעי", "לילה"),
    ],
    "לב": [
    ("שישי", "לילה"),
    ("ראשון", "בוקר"), ("שני", "בוקר"), ("שלישי", "בוקר"),
    ("רביעי", "בוקר"), ("חמישי", "בוקר"), ("שישי", "בוקר"), ("שבת", "בוקר"),
    ("ראשון", "ערב"), ("שני", "ערב"), ("שלישי", "ערב"),
    ("רביעי", "ערב"), ("חמישי", "ערב"), ("שישי", "ערב"), ("שבת", "ערב"),
],
    "איתי": [
    ("ראשון", "בוקר"), ("שני", "בוקר"), ("שלישי", "בוקר"),
    ("רביעי", "בוקר"), ("חמישי", "בוקר"), ("שישי", "בוקר"), ("שבת", "בוקר"),
    ("ראשון", "ערב"), ("שני", "ערב"), ("שלישי", "ערב"),
    ("רביעי", "ערב"), ("חמישי", "ערב"), ("שישי", "ערב"), ("שבת", "ערב"),
],  
    "אלינור": [
    ("ראשון", "בוקר"), ("שני", "בוקר"), ("שלישי", "בוקר"),
    ("רביעי", "בוקר"), ("חמישי", "בוקר"), ("שישי", "בוקר"), ("שבת", "בוקר"),
    ("ראשון", "ערב"), ("שני", "ערב"), ("שלישי", "ערב"),
    ("רביעי", "ערב"), ("חמישי", "ערב"), ("שישי", "ערב"), ("שבת", "ערב"),
],
    "גיא": [
    ("ראשון", "בוקר"), ("שני", "בוקר"), ("שלישי", "בוקר"),
    ("רביעי", "בוקר"), ("חמישי", "בוקר"), ("שישי", "בוקר"), ("שבת", "בוקר"),
],
}

NIGHT_LOVERS = {"לב", "איתי", "גיא", "אלינור"}
DIVERSE_AGENTS = {"שני", "רונית", "לירון"}
NO_12_HOUR     = {"ריקי", "סימה"}

AGENT_COLORS = {
    "לב":     "#FFB3B3",
    "איתי":   "#FFD9B3",
    "גיא":    "#FFFBB3",
    "אלינור": "#B3FFB3",
    "שרית":   "#B3D9FF",
    "רונית":  "#D9B3FF",
    "שני":    "#FFB3E6",
    "ריקי":   "#B3FFF0",
    "אדיר":   "#FFE0B3",
    "טלי":    "#E0B3FF",
    "סימה":   "#FFD6D6",
    "לירון":  "#C8E6C9",
}


def generate_schedule(
    agents: List[Dict],
    days: List[str],
    is_fourth_saturday: bool = True,
    extra_forbidden: Dict = None,
    day_off: Dict = None,
    twelve_hour: Dict = None,
    pref_days: Dict = None,
) -> pd.DataFrame:
    names  = [a["name"] for a in agents if a.get("status", "פעיל") == "פעיל"]
    totals = {a["name"]: a["total"] for a in agents}

    forbidden_local = copy.deepcopy(FORBIDDEN_DEFAULT)

    if extra_forbidden:
        for name, lst in extra_forbidden.items():
            if name not in forbidden_local:
                forbidden_local[name] = []
            forbidden_local[name].extend(lst)

    if day_off:
        for name, off_days in day_off.items():
            if name not in forbidden_local:
                forbidden_local[name] = []
            for d in off_days:
                for s in SHIFTS:
                    forbidden_local[name].append((d, s))

    if is_fourth_saturday:
        totals["ריקי"] = 4
        forbidden_local["ריקי"] = [
            d for d in forbidden_local.get("ריקי", []) if d[0] != "שבת"
        ]

    twelve = twelve_hour or {}
    pref = pref_days or {}
    def pref_score(name, day, shift):
        days_pref = pref.get(name, {}).get(shift, [])
        return 0 if day in days_pref else 1
        
    schedule: Dict[str, Dict[str, str]] = {n: {d: "—" for d in DAYS_ORDER} for n in names}
    assigned_count: Dict[str, int]      = {n: 0 for n in names}
    shift_type_count: Dict[str, Dict[str, int]] = {
        n: {"בוקר": 0, "ערב": 0, "לילה": 0} for n in names
    }

    def is_forbidden(name, day, shift):
        return any(fd == day and fs == shift for (fd, fs) in forbidden_local.get(name, []))

    def can_assign(name, day, shift):
        if assigned_count[name] >= totals[name]:
            return False
        if schedule[name][day] != "—":
            return False
        if is_forbidden(name, day, shift):
            return False
        day_idx = DAYS_ORDER.index(day)
        if shift == "בוקר" and day_idx > 0:
            if schedule[name][DAYS_ORDER[day_idx - 1]] == "לילה":
                return False
        # חוק שישי/שבת – עדיפות, לא חובה מוחלטת
        # שישי ערב/לילה חוסם שבת
        if day == "שישי" and shift in ("ערב", "לילה") and schedule[name]["שבת"] != "—":
            return False
        if day == "שבת" and schedule[name]["שישי"] in ("ערב", "לילה"):
            return False
        return True

    def can_assign_relaxed(name, day, shift):
        """ללא חוק שישי/שבת – לשימוש בשלב השלמה"""
        if assigned_count[name] >= totals[name]:
            return False
        if schedule[name][day] != "—":
            return False
        if is_forbidden(name, day, shift):
            return False
        day_idx = DAYS_ORDER.index(day)
        if shift == "בוקר" and day_idx > 0:
            if schedule[name][DAYS_ORDER[day_idx - 1]] == "לילה":
                return False
        return True

    def assign(name, day, shift):
        schedule[name][day] = shift
        assigned_count[name] += 1
        shift_type_count[name][shift] += 1

    def diversity_score(name, shift):
        return shift_type_count[name][shift]

    def required_evening(day):
        twelve_morning = sum(
            1 for n in names
            if schedule[n][day] == "בוקר"
            and twelve.get(f"{n}_{day}", False)
            and n not in NO_12_HOUR
        )
        return max(0, REQUIRED_PER_SHIFT[day]["ערב"] - twelve_morning)

    def fill_shift(day, shift, needed, use_relaxed=False):
        """ממלא משמרת עד הכמות הנדרשת"""
        if shift == "לילה":
            primary = [n for n in names if n in NIGHT_LOVERS]
        elif shift == "בוקר":
            primary = [n for n in names if n not in NIGHT_LOVERS and n not in DIVERSE_AGENTS]
        else:
            primary = [n for n in names if n not in NIGHT_LOVERS]

        def sort_key(n):
            base   = 0 if n in primary else 1
            div    = diversity_score(n, shift) if n in DIVERSE_AGENTS else 0
            pref_s = pref_score(n, day, shift)
            return (base, pref_s, div, assigned_count[n])

        ordered = sorted(names, key=sort_key)
        check   = can_assign_relaxed if use_relaxed else can_assign

        filled = 0
        # סיבוב ראשון – עם הגבלת פיזור
        for agent_name in ordered:
            if filled >= needed:
                break
            if check(agent_name, day, shift) and shift_type_count[agent_name][shift] < 3:
                assign(agent_name, day, shift)
                filled += 1

        # סיבוב שני – בלי הגבלת פיזור
        if filled < needed:
            for agent_name in ordered:
                if filled >= needed:
                    break
                if check(agent_name, day, shift):
                    assign(agent_name, day, shift)
                    filled += 1

        return filled

    # ── שלב 1: משמרות קבועות ──
    for agent_name, fixed in FIXED_SHIFTS.items():
        if agent_name not in names:
            continue
        for day, shift in fixed.items():
            if can_assign_relaxed(agent_name, day, shift):
                assign(agent_name, day, shift)

    # ── שלב 2: מילוי שישי ושבת קודם ──
    for day in ["שישי", "שבת"]:
        for shift in SHIFTS:
            if shift == "ערב":
                required = required_evening(day)
            else:
                required = REQUIRED_PER_SHIFT[day][shift]
            already = sum(1 for n in names if schedule[n][day] == shift)
            needed  = required - already
            if needed > 0:
                fill_shift(day, shift, needed, use_relaxed=False)

    # ── שלב 3: מילוי ימי חול ──
    for day in ["ראשון", "שני", "שלישי", "רביעי", "חמישי"]:
        for shift in SHIFTS:
            if shift == "ערב":
                required = required_evening(day)
            else:
                required = REQUIRED_PER_SHIFT[day][shift]
            already = sum(1 for n in names if schedule[n][day] == shift)
            needed  = required - already
            if needed > 0:
                fill_shift(day, shift, needed, use_relaxed=False)

   # ── שלב 4: השלמה למכסה – ימי חול בלבד, רק במשמרות שיש בהן מקום ──
    for agent_name in names:
        if assigned_count[agent_name] >= totals[agent_name]:
            continue
        # רק ימי חול א'-ה'
        for day in ["ראשון", "שני", "שלישי", "רביעי", "חמישי"]:
            if assigned_count[agent_name] >= totals[agent_name]:
                break
            if schedule[agent_name][day] != "—":
                continue
            if agent_name in DIVERSE_AGENTS:
                shift_order = sorted(SHIFTS, key=lambda s: shift_type_count[agent_name][s])
            elif agent_name in NIGHT_LOVERS:
                shift_order = sorted(SHIFTS, key=lambda s: (0 if s == "לילה" else 1, shift_type_count[agent_name][s]))
            else:
                shift_order = sorted(SHIFTS, key=lambda s: shift_type_count[agent_name][s])

            for shift in shift_order:
                if not can_assign(agent_name, day, shift):
                    continue
                current_count = sum(1 for n in names if schedule[n][day] == shift)
                if shift == "ערב":
                    max_allowed = required_evening(day)
                else:
                    max_allowed = REQUIRED_PER_SHIFT[day][shift]
                if current_count >= max_allowed:
                    continue
                assign(agent_name, day, shift)
                break



    rows = []
    for agent_name in names:
        row = {"שם": agent_name}
        for day in DAYS_ORDER:
            row[day] = schedule[agent_name][day]
        row["סה״כ"] = assigned_count[agent_name]
        rows.append(row)

    return pd.DataFrame(rows)
