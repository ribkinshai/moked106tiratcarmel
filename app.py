import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import streamlit.components.v1 as components
from scheduler import generate_schedule, AGENT_COLORS, SHIFT_HOURS, DAYS_ORDER, SHIFTS, NO_12_HOUR
from archive import load_archive, save_to_archive, delete_from_archive, archive_to_df
from current_state import save_current, load_current

st.set_page_config(
    page_title="סידור עבודה – מוקד 106",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Heebo', sans-serif; direction: rtl; }
    .main { background-color: #f8f9fc; }

    /* ===== Sidebar - כל הסלקטורים האפשריים ===== */
    section[data-testid="stSidebar"][aria-expanded="true"],
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 50%, #f093fb 100%) !important;
    }

    /* הסתר רוח רפאים של הסיידבר כשסגור */
    section[data-testid="stSidebar"][aria-expanded="false"],
    section[data-testid="stSidebar"][aria-expanded="false"] *,
    [data-testid="stSidebar"][aria-expanded="false"] > div,
    [data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
        background: transparent !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        visibility: hidden !important;
        overflow: hidden !important;
        padding: 0 !important;
        border: none !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: white !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        text-shadow: 0 2px 8px rgba(0,0,0,0.2);
        font-weight: 800 !important;
    }

    [data-testid="stSidebar"] details,
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background: rgba(255,255,255,0.15) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.25) !important;
        margin-bottom: 8px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea {
        background: rgba(255,255,255,0.95) !important;
        color: #3d3d5c !important;
        border-radius: 10px !important;
        border: none !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.3) !important;
    }

    /* כפתור סגירה/פתיחה של הסיידבר - הופך כיוון */
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="collapsedControl"],
    [data-testid="baseButton-header"],
    [data-testid="baseButton-headerNoPadding"],
    button[kind="header"],
    button[kind="headerNoPadding"] {
        transform: scaleX(-1) !important;
    }

    /* כפתורים ראשיים */
    .stButton > button {
        background: linear-gradient(135deg,#7c6fc4,#5c4fa4); color:white !important;
        border-radius:10px; border:none;
        font-family:'Heebo',sans-serif; font-weight:600;
        box-shadow: 0 4px 15px rgba(124,111,196,0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(124,111,196,0.4);
    }
    .alert-box {
        background:#fff3cd; border:1px solid #ffc107; border-radius:8px;
        padding:10px 16px; margin:8px 0; color:#856404; direction:rtl;
    }

    /* כפתורים זוהרים בהובר */
    .stButton > button:hover {
        box-shadow: 0 0 25px rgba(124,111,196,0.6), 0 6px 20px rgba(124,111,196,0.4) !important;
    }
    /* טאבים עם זוהר */
    button[data-baseweb="tab"]:hover {
        text-shadow: 0 0 12px rgba(124,111,196,0.6);
    }
/* Mobile responsive */
    @media (max-width: 768px) {
        h1 { font-size: 22px !important; }
        h2 { font-size: 18px !important; }
        h3 { font-size: 16px !important; }
        .stButton > button {
            font-size: 13px !important;
            padding: 8px 12px !important;
        }
        [data-testid="stMetric"] {
            padding: 8px !important;
        }
        /* טבלת הסידור */
        table th { font-size: 11px !important; padding: 6px !important; }
        table td { font-size: 10px !important; padding: 6px !important; min-width: 70px !important; }
        /* סיידבר ברוחב מלא בנייד */
        section[data-testid="stSidebar"][aria-expanded="true"] {
            width: 90vw !important;
        }
    }
    @media (max-width: 480px) {
        h1 { font-size: 18px !important; }
        table td { font-size: 9px !important; min-width: 60px !important; }
    }
</style>

""", unsafe_allow_html=True)

if "agents" not in st.session_state:
    st.session_state.agents = [
        {"name": "לב",    "total": 5, "pref": "לילה",     "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("לב","#ccc")},
        {"name": "איתי",  "total": 3, "pref": "לילה",     "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("איתי","#ccc")},
        {"name": "גיא",   "total": 5, "pref": "לילה",     "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("גיא","#ccc")},
        {"name": "אלינור","total": 3, "pref": "לילה",     "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("אלינור","#ccc")},
        {"name": "שרית",  "total": 5, "pref": "בוקר/ערב", "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("שרית","#ccc")},
        {"name": "רונית", "total": 4, "pref": "פיזור",    "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("רונית","#ccc")},
        {"name": "שני",   "total": 5, "pref": "פיזור",    "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("שני","#ccc")},
        {"name": "ריקי",  "total": 3, "pref": "בוקר",     "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("ריקי","#ccc")},
        {"name": "אדיר",  "total": 5, "pref": "ללא העדפה","status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("אדיר","#ccc")},
        {"name": "טלי",   "total": 5, "pref": "ללא העדפה","status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("טלי","#ccc")},
        {"name": "סימה",  "total": 2, "pref": "ערב",      "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("סימה","#ccc")},
        {"name": "לירון", "total": 5, "pref": "פיזור",    "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("לירון","#ccc")},
    ]

defaults = {
    "schedule_df": None, "edit_mode": False,
    "fourth_saturday": True, "week_notes": "",
    "week_label": "", "twelve_hour": {},
    "cell_notes": {}, "watcher": {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
# טעינה אוטומטית בפתיחה
if "loaded" not in st.session_state:
    st.session_state.loaded = True
    saved = load_current()
    if saved:
        if saved.get("schedule") is not None:
            st.session_state.schedule_df = saved["schedule"]
        st.session_state.twelve_hour = saved.get("twelve_hour", {})
        st.session_state.watcher     = saved.get("watcher", {})
        st.session_state.cell_notes  = saved.get("cell_notes", {})
        st.session_state.week_label  = saved.get("week_label", "")
        st.session_state.week_notes  = saved.get("week_notes", "")
def get_next_week_label():
    today = datetime.now()
    days_until_sunday = (6 - today.weekday()) % 7
    if days_until_sunday == 0:
        days_until_sunday = 7
    next_sunday = today + timedelta(days=days_until_sunday)
    next_saturday = next_sunday + timedelta(days=6)
    return f"{next_sunday.day}-{next_saturday.day}/{next_saturday.month}"

def get_week_dates():
    today = datetime.now()
    days_until_sunday = (6 - today.weekday()) % 7
    if days_until_sunday == 0:
        days_until_sunday = 7
    next_sunday = today + timedelta(days=days_until_sunday)
    return [(next_sunday + timedelta(days=i)) for i in range(7)]
SHIFT_CLASS  = {"בוקר": "cell-morning", "ערב": "cell-noon", "לילה": "cell-night"}
SHIFT_EMOJI = {
    "בוקר": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="vertical-align:middle"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>',
    "ערב":  '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="vertical-align:middle"><path d="M2 12h20M12 2a10 10 0 0 1 10 10M5 18a7 7 0 0 1 14 0"/></svg>',
    "לילה": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="vertical-align:middle"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
}
STATUS_OPTIONS = ["פעיל", "חופשה", "מחלה"]
SHIFT_OPTIONS  = ["בוקר", "ערב", "לילה", "—"]

with st.sidebar:
    st.markdown("## ⚙️ הגדרות שבוע")
    st.session_state.week_label = st.text_input(
        "תווית שבוע", value=st.session_state.week_label)
    st.session_state.week_notes = st.text_area(
        "הערות שבועיות", value=st.session_state.week_notes, height=80)
    st.session_state.fourth_saturday = st.toggle(
        "שבת רביעית (ריקי עובדת)", value=st.session_state.fourth_saturday)

    st.divider()
    st.markdown("## 👥 הגדרות נציגים")
    updated_agents = []
    for i, agent in enumerate(st.session_state.agents):
        with st.expander(f"{'🟢' if agent['status']=='פעיל' else '🔴'} {agent['name']}", expanded=False):
            status  = st.selectbox("סטטוס", STATUS_OPTIONS,
                                    index=STATUS_OPTIONS.index(agent.get("status","פעיל")),
                                    key=f"status_{i}")
            total   = st.number_input("מכסה שבועית", 1, 7,
                                       value=agent["total"], key=f"total_{i}")
            day_off = st.multiselect("ימי חופש קבועים", DAYS_ORDER,
                                      default=agent.get("day_off",[]), key=f"dayoff_{i}")
            st.markdown("**ימים מועדפים:**")
            pref_morning = st.multiselect("☀️ בוקר", DAYS_ORDER,
                                           default=agent.get("pref_morning",[]), key=f"pm_{i}")
            pref_evening = st.multiselect("🌤 ערב",  DAYS_ORDER,
                                           default=agent.get("pref_evening",[]), key=f"pe_{i}")
            pref_night   = st.multiselect("🌙 לילה", DAYS_ORDER,
                                           default=agent.get("pref_night",[]),   key=f"pn_{i}")
            # שבת רביעית – אוטומטי לפי היסטוריה או ידני
            recent_3 = load_archive()[:3]
            auto_4th = False
            if len(recent_3) >= 3:
                worked_weekend = 0
                weekend_shifts = [("שישי","ערב"), ("שישי","לילה"), ("שבת","בוקר"), ("שבת","ערב")]
                for entry in recent_3:
                    for row in entry.get("schedule", []):
                        if row["שם"] != agent["name"]:
                            continue
                        if any(row.get(d) == s for d, s in weekend_shifts):
                            worked_weekend += 1
                            break
                if worked_weekend >= 3:
                    auto_4th = True

            current_4th = agent.get("fourth_weekend_off", auto_4th)
            fourth_off = st.toggle(
                f"🛌 שבת רביעית (לא לשבץ סופ״ש)",
                value=current_4th,
                key=f"fourth_{i}",
                help="אסור לשבץ בשישי ערב/לילה ובשבת בוקר/ערב"
            )
            if auto_4th and not current_4th:
                st.caption("⚠️ אוטומטית: עבד 3 סופ\"שים ברצף")
            updated_agents.append({
                **agent,
                "status": status, "total": total, "day_off": day_off,
                "pref_morning": pref_morning,
                "pref_evening": pref_evening,
                "pref_night":   pref_night,
                "fourth_weekend_off": fourth_off,
            })
    st.session_state.agents = updated_agents

    st.divider()
    st.markdown("**מקרא:**")
    st.markdown("🟢 בוקר 07:00-15:00")
    st.markdown("🔵 בוקר 12ש 07:00-19:00")
    st.markdown("🟡 ערב 15:00-23:00")
    st.markdown("🟣 לילה 23:00-07:00")
    st.markdown("🔴 לילה 12ש 19:00-07:00")

tab1, tab2, tab3, tab4 = st.tabs(["📋 סידור", "📊 סטטיסטיקות", "🔍 השוואת שבועות", "🗂 ארכיון"])

with tab1:
    next_week = get_next_week_label()
    st.markdown(f"""
        <div style='text-align:center; padding:20px 0;'>
            <h1 style='margin:0; font-weight:900; font-size:42px; letter-spacing:-1px;'>
                <span style='background:linear-gradient(135deg,#667eea 0%,#764ba2 50%,#f093fb 100%);
                             -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                             background-clip:text;text-shadow:0 4px 20px rgba(102,126,234,0.3);'>
                    מוקד 106
                </span>
                <span style='color:#3d3d5c;font-size:32px;font-weight:600;'>
                    | סידור עבודה שבועי
                </span>
            </h1>
            <h3 style='margin:10px 0 0; color:#7c6fc4; font-weight:600;
                       letter-spacing:2px;'>📅 {next_week}</h3>
        </div>
    """, unsafe_allow_html=True)
    if st.session_state.week_label:
        st.markdown(f"**שבוע:** {st.session_state.week_label}")
    if st.session_state.week_notes:
        st.markdown(f"📝 {st.session_state.week_notes}")

    col1, col2, col3, col4, col5 = st.columns([2,1,1,1,1.5])
    with col1:
        if st.button("⚡ צור סידור אוטומטי", use_container_width=True):
            day_off_map = {a["name"]: a.get("day_off",[]) for a in st.session_state.agents}
            # שבת רביעית - איסורים
            extra_forb_map = {}
            for a in st.session_state.agents:
                if a.get("fourth_weekend_off", False):
                    extra_forb_map[a["name"]] = [
                        ("שישי", "ערב"), ("שישי", "לילה"),
                        ("שבת", "בוקר"), ("שבת", "ערב"),
                    ]
            pref_map = {
                a["name"]: {
                    "בוקר": a.get("pref_morning", []),
                    "ערב":  a.get("pref_evening", []),
                    "לילה": a.get("pref_night",   []),
                }
                for a in st.session_state.agents
            }

            # היסטוריה מ-3 שבועות אחרונים
            recent_archive = load_archive()[:3]
            history_map = {}
            for entry in recent_archive:
                for row in entry.get("schedule", []):
                    name = row["שם"]
                    if name not in history_map:
                        history_map[name] = {"בוקר": 0, "ערב": 0, "לילה": 0}
                    for d in DAYS_ORDER:
                        s = row.get(d, "—")
                        if s in history_map[name]:
                            history_map[name][s] += 1
                            # היסטוריה של שבת לילה – מתי כל נציג עבד לאחרונה (כמה שבועות אחורה)
            all_archive_full = load_archive()
            for name in {row["שם"] for entry in all_archive_full for row in entry.get("schedule", [])}:
                if name not in history_map:
                    history_map[name] = {"בוקר": 0, "ערב": 0, "לילה": 0}
                weeks_ago = 999
                for idx, entry in enumerate(all_archive_full):
                    for row in entry.get("schedule", []):
                        if row["שם"] == name and row.get("שבת") == "לילה":
                            weeks_ago = idx
                            break
                    if weeks_ago != 999:
                        break
                history_map[name]["__sat_night_last__"] = weeks_ago
                            # זיהוי נציגים שעבדו בסופ"ש האחרון – לחסימה השבוע
            last_weekend_workers = set()
            if recent_archive:
                last_entry = recent_archive[0]
                for row in last_entry.get("schedule", []):
                    name = row["שם"]
                    fri_shift = row.get("שישי", "—")
                    sat_shift = row.get("שבת", "—")
                    if fri_shift in ("ערב", "לילה") or sat_shift in ("בוקר", "ערב"):
                        last_weekend_workers.add(name)
            history_map["__last_weekend__"] = last_weekend_workers

            # זיהוי סוג השבוע (A או B) לפי הסידור האחרון בארכיון
            week_type = "A"
            if recent_archive:
                last_entry = recent_archive[0]
                lev_nights = 0
                for row in last_entry.get("schedule", []):
                    if row["שם"] == "לב":
                        lev_nights = sum(1 for d in DAYS_ORDER if row.get(d) == "לילה")
                        break
                # אם בסידור הקודם לב=5 → השבוע הזה A (לב=4, רונית=4)
                # אם בסידור הקודם לב=4 → השבוע הזה B (לב=5, רונית=3)
                week_type = "A" if lev_nights >= 5 else "B"

            with st.spinner("מחשב סידור..."):
                df = generate_schedule(
                    st.session_state.agents, DAYS_ORDER,
                    is_fourth_saturday=st.session_state.fourth_saturday,
                    day_off=day_off_map,
                    twelve_hour=st.session_state.twelve_hour,
                    pref_days=pref_map,
                    recent_history=history_map,
                    extra_forbidden=extra_forb_map,
                    week_type=week_type,
                )
                st.session_state.schedule_df = df
                st.session_state.edit_mode   = False
            st.success("הסידור נוצר! ✅")
    with col2:
        if st.session_state.schedule_df is not None:
            if st.button("✏️ עריכה", use_container_width=True):
                st.session_state.edit_mode = not st.session_state.edit_mode
    with col3:
        if st.session_state.schedule_df is not None:
            if st.button("🔄 אפס", use_container_width=True):
                st.session_state.schedule_df = None
                st.session_state.edit_mode   = False
                st.rerun()
    with col4:
        if st.session_state.schedule_df is not None and st.session_state.week_label:
            if st.button("💾 שמור לארכיון", use_container_width=True):
                save_to_archive(st.session_state.schedule_df,
                                st.session_state.week_label,
                                st.session_state.week_notes)
                st.success("נשמר! ✅")
    with col5:
        archive_for_load = load_archive()
        if archive_for_load:
            week_options = ["— בחר —"] + [e["week"] for e in archive_for_load]
            chosen = st.selectbox("📂 טען מארכיון", week_options,
                                   key="load_archive_select",
                                   label_visibility="collapsed")
            if chosen != "— בחר —":
                entry = next((e for e in archive_for_load if e["week"] == chosen), None)
                if entry and st.button("📂 טען", use_container_width=True, key="load_archive_btn"):
                    st.session_state.schedule_df = archive_to_df(entry)
                    st.session_state.week_label = entry["week"]
                    st.session_state.week_notes = entry.get("notes", "")
                    st.success(f"נטען: {chosen} ✅")
                    st.rerun()
    if st.session_state.schedule_df is not None:
        df = st.session_state.schedule_df
        alerts = []
        from scheduler import REQUIRED_PER_SHIFT
        for day in DAYS_ORDER:
            for shift in SHIFTS:
                count    = len(df[df[day] == shift])
                required = REQUIRED_PER_SHIFT[day][shift]
                if shift == "ערב":
                    twelve_count = sum(
                        1 for n in df["שם"].tolist()
                        if df[df["שם"]==n][day].values[0] == "בוקר"
                        and st.session_state.twelve_hour.get(f"{n}_{day}", False)
                        and n not in NO_12_HOUR
                    )
                    required = max(0, required - twelve_count)
                if count < required:
                    alerts.append(f"⚠️ {day} – {shift}: {count}/{required} נציגים")
        # התראות על משמרות חוזרות
        exempt_agents = {"גיא", "לב", "סימה", "אלינור", "איתי", "שרית", "ריקי", "אדיר"}
        recent_archive = load_archive()[:3]
        history_map = {}
        for entry in recent_archive:
            for row in entry.get("schedule", []):
                name = row["שם"]
                if name not in history_map:
                    history_map[name] = {"בוקר": 0, "ערב": 0, "לילה": 0}
                for d in DAYS_ORDER:
                    s = row.get(d, "—")
                    if s in history_map[name]:
                        history_map[name][s] += 1

        # בדיקה לשבוע הנוכחי
        for _, row in df.iterrows():
            name = row["שם"]
            if name in exempt_agents:
                continue
            if name not in history_map:
                continue
            for shift in ["ערב", "לילה"]:
                current_count = sum(1 for d in DAYS_ORDER if row[d] == shift)
                past_count = history_map[name].get(shift, 0)
                total = current_count + past_count
                if past_count >= 3 and current_count >= 2:
                    alerts.append(
                        f"🔁 {name} עבד {past_count} משמרות {shift} ב-3 שבועות אחרונים "
                        f"וגם השבוע {current_count} – שווה לשקול לשנות"
                    )
        if alerts:
            st.markdown("### ⚠️ התראות")
            for a in alerts:
                st.markdown(f"<div class='alert-box'>{a}</div>", unsafe_allow_html=True)

    if st.session_state.schedule_df is not None and st.session_state.edit_mode:
        st.markdown("### ✏️ עריכה ידנית")
        df = st.session_state.schedule_df

        # הצג טבלה כרגיל
        week_dates = get_week_dates()
        header_html = "".join(
            f"<th>{day}<br><span style='font-size:11px;font-weight:400;opacity:0.7'>"
            f"{week_dates[i].day}/{week_dates[i].month}</span></th>"
            for i, day in enumerate(DAYS_ORDER)
        )
        rows_html   = ""
        for shift in SHIFTS:
            sc    = SHIFT_CLASS[shift]
            emoji = SHIFT_EMOJI[shift]
            hours = SHIFT_HOURS[shift]
            rows_html += "<tr>"
            for day in DAYS_ORDER:
                agents_in_shift = df[df[day] == shift]["שם"].tolist()
                cells = []
                for ag in agents_in_shift:
                    color = AGENT_COLORS.get(ag, "#eee")
                    key   = f"{ag}_{day}"
                    is_12 = st.session_state.twelve_hour.get(key, False)
                    if is_12 and ag not in NO_12_HOUR:
                        if shift == "בוקר":
                            hours_display = " 07:00-19:00"
                        elif shift == "לילה":
                            hours_display = " 19:00-07:00"
                        else:
                            hours_display = ""
                    else:
                        hours_display = ""
                    watcher_key   = f"{day}_{shift}"
                    is_watcher    = st.session_state.watcher.get(watcher_key) == ag
                    watcher_badge = " 👁" if is_watcher else ""
                    cells.append(
                        f"<span style='background:{color};border-radius:6px;"
                        f"padding:3px 12px;display:inline-block;margin:6px 2px 2px 2px;"
                        "font-size:14px;font-weight:600;'>"
                        f"{ag}{watcher_badge}"
                        f"<span style='font-weight:400;font-size:10px;color:#555'>{hours_display}</span>"
                        f"</span>"
                    )
                agents_str = "<br>".join(cells) if cells else "<span style='color:#bbb'>—</span>"
                rows_html += (
                    f"<td class='{sc}'>"
                    f"<b>{emoji} {shift}</b><br>"
                    f"<small style='opacity:.7'>{hours}</small><br><br>"
                    f"{agents_str}</td>"
                )
            rows_html += "</tr>"

        full_html = f"""
        <html><head><style>
            @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700;800&display=swap');
            body {{
                font-family:'Heebo',sans-serif; direction:rtl; margin:0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                overflow-x: auto;
            }}
            table {{
                width:100%; border-collapse:separate; border-spacing:6px;
                min-width: 900px;
            }}
            th {{
                background: linear-gradient(180deg, #ffffff 0%, #e8e4f8 100%);
                color:#3d3d5c; padding:16px; border-radius:12px;
                font-weight:800; text-shadow:1px 1px 0 white;
                box-shadow: 0 6px 0 #5c4fa4, 0 10px 20px rgba(0,0,0,0.2);
                text-align:center; font-size:14px;
            }}
            td {{
                padding:16px; border-radius:12px; vertical-align:top;
                min-width:110px;
                box-shadow: 0 6px 0 rgba(0,0,0,0.15), 0 10px 20px rgba(0,0,0,0.1);
                text-align:center;
            }}
            .cell-morning {{
                background: linear-gradient(180deg, #b8f2c1 0%, #6ee7b7 100%);
                color:#064e3b;
            }}
            .cell-noon    {{
                background: linear-gradient(180deg, #fde68a 0%, #f59e0b 100%);
                color:#78350f;
            }}
            .cell-night   {{
                background: linear-gradient(180deg, #c4b5fd 0%, #8b5cf6 100%);
                color:#2e1065;
            }}
            td b {{ font-weight:800; font-size:14px; }}
            small {{ font-size:11px; opacity:0.8; }}
            span[style*="background"] {{
                background: linear-gradient(180deg, white, #f5f5fa) !important;
                color:#3d3d5c !important;
                box-shadow: 0 3px 0 rgba(0,0,0,0.15), 0 5px 10px rgba(0,0,0,0.1);
                border-radius:10px !important;
                padding:6px 10px !important;
                font-weight:700 !important;
            }}
        </style></head><body>
        <table>
            <thead><tr>{header_html}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        </body></html>
        """
        components.html(full_html, height=750, scrolling=True)

        # ── לוח עריכה ──
        st.markdown("---")
        edited_data = {row["שם"]: dict(row) for _, row in df.iterrows()}
        all_agents  = [a["name"] for a in st.session_state.agents
                       if a.get("status","פעיל") == "פעיל"]

        # נציג רואה אוטומטי – הראשון בכל משמרת
        for day in DAYS_ORDER:
            for shift in SHIFTS:
                key = f"{day}_{shift}"
                agents_in = df[df[day] == shift]["שם"].tolist()
                if agents_in and st.session_state.watcher.get(key, "—") == "—":
                    st.session_state.watcher[key] = agents_in[0]

        for day in DAYS_ORDER:
            with st.expander(f"📅 {day}", expanded=True):
                for shift in SHIFTS:
                    emoji     = SHIFT_EMOJI[shift]
                    agents_in = df[df[day] == shift]["שם"].tolist()
                    free_agents = [n for n in all_agents
                                   if edited_data[n].get(day,"—") == "—"]

                    watcher_key     = f"{day}_{shift}"
                    current_watcher = st.session_state.watcher.get(watcher_key, "—")

                    cols = st.columns([0.8] + [1.2]*max(len(agents_in), 1) + [0.8])
                    cols[0].markdown(
                        f"<div style='padding-top:8px;font-weight:700;"
                        f"font-size:13px'>{emoji} {shift}</div>",
                        unsafe_allow_html=True)

                    for i, ag in enumerate(agents_in):
                        with cols[i+1]:
                            ag_color    = AGENT_COLORS.get(ag, "#eee")
                            is_watcher  = (current_watcher == ag)
                            watcher_tag = " 👁" if is_watcher else ""

                            # שם נציג
                            key_12     = f"{ag}_{day}"
                            is_12      = st.session_state.twelve_hour.get(key_12, False)
                            hours_tag  = ""
                            if is_12 and shift in ("בוקר","לילה") and ag not in NO_12_HOUR:
                                hours_tag = " 07:00-19:00" if shift=="בוקר" else " 19:00-07:00"

                            st.markdown(
                                f"<div style='background:{ag_color};border-radius:6px;"
                                f"padding:2px 6px;text-align:center;font-size:12px;"
                                f"font-weight:700'>{ag}{watcher_tag}"
                                f"<br><span style='font-size:10px;color:#555;font-weight:400'>"
                                f"{hours_tag}</span></div>",
                                unsafe_allow_html=True)

                            # dropdown להחלפה
                            options  = [ag] + [n for n in free_agents if n != ag]
                            selected = st.selectbox("", options,
                                                     key=f"sel_{ag}_{day}_{shift}",
                                                     label_visibility="collapsed")
                            if selected != ag:
                                edited_data[ag][day]       = "—"
                                edited_data[selected][day] = shift

                            # כפתור הסרה
                            if st.button("✖", key=f"remove_{ag}_{day}_{shift}",
                                         help=f"הסר {ag} מ{shift} {day}"):
                                edited_data[ag][day] = "—"
                                if current_watcher == ag:
                                    remaining = [a for a in agents_in if a != ag]
                                    st.session_state.watcher[watcher_key] = remaining[0] if remaining else "—"
                                new_rows = []
                                for a in all_agents:
                                    if a in edited_data:
                                        row = edited_data[a]
                                        row["סה״כ"] = sum(1 for d in DAYS_ORDER if row.get(d,"—") != "—")
                                        new_rows.append(row)
                                st.session_state.schedule_df = pd.DataFrame(new_rows)
                                st.rerun()

                            # 12 שעות
                            if shift in ("בוקר","לילה") and ag not in NO_12_HOUR:
                                checked = st.checkbox("⏱12ש", value=is_12,
                                                       key=f"12h_{ag}_{day}")
                                if checked != is_12:
                                    st.session_state.twelve_hour[key_12] = checked
                                    st.rerun()

                            # שינוי נציג רואה
                            if st.button("👁 רואה", key=f"watch_{ag}_{day}_{shift}"):
                                st.session_state.watcher[watcher_key] = ag
                                st.rerun()

                    # הוספת נציג – מחולק לרשימת המתנה ופנויים
                    with cols[len(agents_in)+1]:
                        if free_agents:
                            # רשימת המתנה – נציגים שלא הגיעו למכסה
                            waiting_list = []
                            available = []
                            for n in free_agents:
                                ag_obj = next((a for a in st.session_state.agents
                                                if a["name"] == n), None)
                                if ag_obj:
                                    n_total = ag_obj.get("total", 0)
                                    filled  = sum(1 for d in DAYS_ORDER
                                                  if edited_data[n].get(d,"—") != "—")
                                    if filled < n_total:
                                        waiting_list.append((n, n_total - filled))
                                    else:
                                        available.append(n)

                            # מיון רשימת המתנה לפי מי שחסר לו הכי הרבה
                            waiting_list.sort(key=lambda x: x[1], reverse=True)

                            options = ["—"]
                            if waiting_list:
                                options.append("━━ רשימת המתנה ━━")
                                for n, missing in waiting_list:
                                    options.append(f"⏳ {n} (חסר {missing})")
                            if available:
                                options.append("━━ פנויים ━━")
                                options.extend(available)

                            add = st.selectbox("➕", options,
                                               key=f"add_{day}_{shift}",
                                               label_visibility="collapsed")

                            # נקה את הטקסט המעוצב
                            clean_name = add
                            if add.startswith("⏳ "):
                                clean_name = add.replace("⏳ ", "").split(" (חסר")[0]

                            if add != "—" and not add.startswith("━━"):
                                if clean_name in [n for n, _ in waiting_list] or clean_name in available:
                                    edited_data[clean_name][day] = shift
                                    new_rows = []
                                    for a in all_agents:
                                        if a in edited_data:
                                            row = edited_data[a]
                                            row["סה״כ"] = sum(1 for d in DAYS_ORDER if row.get(d,"—") != "—")
                                            new_rows.append(row)
                                    st.session_state.schedule_df = pd.DataFrame(new_rows)
                                    st.rerun()
                            if add != "—":
                                edited_data[add][day] = shift
                                new_rows = []
                                for a in all_agents:
                                    if a in edited_data:
                                        row = edited_data[a]
                                        row["סה״כ"] = sum(1 for d in DAYS_ORDER if row.get(d,"—") != "—")
                                        new_rows.append(row)
                                st.session_state.schedule_df = pd.DataFrame(new_rows)
                                st.rerun()

        st.divider()
        if st.button("💾 שמור שינויים", type="primary"):
            new_rows = []
            for ag in all_agents:
                if ag in edited_data:
                    row = edited_data[ag]
                    row["סה״כ"] = sum(1 for d in DAYS_ORDER if row.get(d,"—") != "—")
                    new_rows.append(row)
            new_df = pd.DataFrame(new_rows)
            st.session_state.schedule_df = new_df
            st.session_state.edit_mode   = False
            save_current(
                new_df,
                st.session_state.twelve_hour,
                st.session_state.watcher,
                st.session_state.cell_notes,
                st.session_state.week_label,
                st.session_state.week_notes,
            )
            st.success("נשמר! ✅")
            st.rerun()

    elif st.session_state.schedule_df is not None:
        df     = st.session_state.schedule_df
        twelve = st.session_state.twelve_hour

        week_dates = get_week_dates()
        header_html = "".join(
            f"<th>{day}<br><span style='font-size:11px;font-weight:400;opacity:0.7'>"
            f"{week_dates[i].day}/{week_dates[i].month}</span></th>"
            for i, day in enumerate(DAYS_ORDER)
        )
        rows_html   = ""

        for shift in SHIFTS:
            sc    = SHIFT_CLASS[shift]
            emoji = SHIFT_EMOJI[shift]
            hours = SHIFT_HOURS[shift]
            rows_html += "<tr>"
            for day in DAYS_ORDER:
                agents_in_shift = df[df[day] == shift]["שם"].tolist()
                cells = []
                for ag in agents_in_shift:
                    color     = AGENT_COLORS.get(ag, "#eee")
                    note      = st.session_state.cell_notes.get(f"{ag}_{day}", "")
                    note_html = f"<br><small style='color:#888'>📝{note}</small>" if note else ""

                    key_12 = f"{ag}_{day}"
                    is_12  = st.session_state.twelve_hour.get(key_12, False)
                    hours_tag = ""
                    if is_12 and ag not in NO_12_HOUR:
                        if shift == "בוקר":
                            hours_tag = " 07:00-19:00"
                        elif shift == "לילה":
                            hours_tag = " 19:00-07:00"

                    watcher_key   = f"{day}_{shift}"
                    is_watcher    = st.session_state.watcher.get(watcher_key) == ag
                    watcher_badge = " 👁" if is_watcher else ""

                    cells.append(
                        f"<span style='background:{color};border-radius:6px;"
                        f"padding:3px 8px;display:inline-block;margin:2px;"
                        "font-size:14px;font-weight:600'>"
                        f"{ag}{watcher_badge}"
                        f"<span style='font-weight:400;font-size:10px;color:#555'>{hours_tag}</span>"
                        f"{note_html}</span>"
                    )
                agents_str = "<br>".join(cells) if cells else "<span style='color:#bbb'>—</span>"
                rows_html += (
                    f"<td class='{sc}'>"
                    f"<b>{emoji} {shift}</b><br>"
                    f"<small style='opacity:.7'>{hours}</small><br><br>"
                    f"{agents_str}</td>"
                )
            rows_html += "</tr>"

        full_html = f"""
        <html><head><style>
            @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700;800&display=swap');
            body {{
                font-family:'Heebo',sans-serif; direction:rtl; margin:0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                overflow-x: auto;
            }}
            table {{
                width:100%; border-collapse:separate; border-spacing:6px;
                min-width: 900px;
            }}
            th {{
                background: linear-gradient(180deg, #ffffff 0%, #e8e4f8 100%);
                color:#3d3d5c; padding:16px; border-radius:12px;
                font-weight:800; text-shadow:1px 1px 0 white;
                box-shadow: 0 6px 0 #5c4fa4, 0 10px 20px rgba(0,0,0,0.2);
                text-align:center; font-size:14px;
            }}
            td {{
                padding:16px; border-radius:12px; vertical-align:top;
                min-width:110px;
                box-shadow: 0 6px 0 rgba(0,0,0,0.15), 0 10px 20px rgba(0,0,0,0.1);
                text-align:center;
            }}
            .cell-morning {{
                background: linear-gradient(180deg, #b8f2c1 0%, #6ee7b7 100%);
                color:#064e3b;
            }}
            .cell-noon    {{
                background: linear-gradient(180deg, #fde68a 0%, #f59e0b 100%);
                color:#78350f;
            }}
            .cell-night   {{
                background: linear-gradient(180deg, #c4b5fd 0%, #8b5cf6 100%);
                color:#2e1065;
            }}
            td b {{ font-weight:800; font-size:14px; }}
            small {{ font-size:11px; opacity:0.8; }}
            span[style*="background"] {{
                background: linear-gradient(180deg, white, #f5f5fa) !important;
                color:#3d3d5c !important;
                box-shadow: 0 3px 0 rgba(0,0,0,0.15), 0 5px 10px rgba(0,0,0,0.1);
                border-radius:10px !important;
                padding:6px 10px !important;
                font-weight:700 !important;
            }}
        </style></head><body>
        <table>
            <thead><tr>{header_html}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        </body></html>
        """
        components.html(full_html, height=750, scrolling=True)

        # ── גרסת הדפסה ──
        print_html_inner = f"""<!DOCTYPE html>
<html lang='he' dir='rtl'><head>
<meta charset='UTF-8'>
<title>סידור עבודה - מוקד 106</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700;800&display=swap');
* {{ box-sizing: border-box; -webkit-print-color-adjust:exact !important; print-color-adjust:exact !important; }}
body {{
    font-family:'Heebo',sans-serif; direction:rtl; margin:0; padding:20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}}
.header {{ text-align:center; padding:10px 0; }}
.header h1 {{ margin:0; color:white; font-weight:800; font-size:28px; text-shadow:2px 2px 4px rgba(0,0,0,0.2); }}
.header h2 {{ margin:5px 0 0; color:#fff; font-weight:600; font-size:18px; opacity:0.95; }}
.notes {{ text-align:center; color:white; margin:10px 0; font-size:14px; opacity:0.9; }}
table {{ width:100%; border-collapse:separate; border-spacing:6px; margin-top:15px; }}
th {{
    background: linear-gradient(180deg, #ffffff 0%, #e8e4f8 100%);
    color:#3d3d5c; padding:16px; border-radius:12px;
    font-weight:800; text-shadow:1px 1px 0 white;
    box-shadow: 0 6px 0 #5c4fa4, 0 10px 20px rgba(0,0,0,0.2);
    text-align:center; font-size:14px;
}}
td {{
    padding:16px; border-radius:12px; vertical-align:top;
    min-width:110px; text-align:center;
    box-shadow: 0 6px 0 rgba(0,0,0,0.15), 0 10px 20px rgba(0,0,0,0.1);
}}
.cell-morning {{ background: linear-gradient(180deg, #b8f2c1 0%, #6ee7b7 100%); color:#064e3b; }}
.cell-noon    {{ background: linear-gradient(180deg, #fde68a 0%, #f59e0b 100%); color:#78350f; }}
.cell-night   {{ background: linear-gradient(180deg, #c4b5fd 0%, #8b5cf6 100%); color:#2e1065; }}
td b {{ font-weight:800; font-size:14px; }}
small {{ font-size:11px; opacity:0.8; }}
td span {{
    font-size: 22px !important;
    font-weight: 800 !important;
    padding: 12px 20px !important;
    border-radius: 12px !important;
    background: linear-gradient(180deg, white, #f5f5fa) !important;
    color: #3d3d5c !important;
    box-shadow: 0 3px 0 rgba(0,0,0,0.15), 0 5px 10px rgba(0,0,0,0.1);
    display: inline-block;
    margin: 4px 2px;
}}
td span span {{
    font-size: 14px !important;
    font-weight: 600 !important;
    padding: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    margin: 0 !important;
}}
.print-btn {{
    background:#7c6fc4; color:white; border:none;
    padding:12px 30px; font-size:16px; border-radius:10px;
    cursor:pointer; font-family:'Heebo',sans-serif; font-weight:700;
    margin:15px auto; display:block;
    box-shadow: 0 6px 0 #5c4fa4;
}}
@media print {{
    .print-btn {{ display:none; }}
    @page {{ size: A4 landscape; margin: 0.3cm; }}
    body {{ padding: 5px !important; }}
    .header h1 {{ font-size: 18px !important; }}
    .header h2 {{ font-size: 13px !important; }}
    table {{ border-spacing: 3px !important; }}
    th {{ padding: 6px !important; font-size: 11px !important; }}
    td {{ padding: 6px !important; min-width: 80px !important; }}
    td b {{ font-size: 11px !important; }}
    small {{ font-size: 9px !important; }}
    td span {{
        padding: 8px 14px !important;
        font-size: 18px !important;
        font-weight: 800 !important;
    }}
    td span span {{
        padding: 0 !important;
        font-size: 11px !important;
        font-weight: 600 !important;
    }}
}}
</style></head><body>
<button class='print-btn' onclick='window.print()'>🖨️ הדפס</button>
<div class='header'>
    <h1>📋 מוקד 106 - סידור עבודה שבועי</h1>
    <h2>📅 {next_week}</h2>
</div>
<div class='notes'>{st.session_state.week_notes if st.session_state.week_notes else ''}</div>
<table>
<thead><tr>{header_html}</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</body></html>"""

        st.download_button(
            label="🖨️ הורד גרסת הדפסה (HTML)",
            data=print_html_inner.encode("utf-8"),
            file_name=f"sidur_print_{next_week.replace('/','-')}.html",
            mime="text/html",
        )
        st.caption("💡 לאחר הורדה – פתח את הקובץ בדפדפן ולחץ הדפס. הצבעים יודפסו!")

        with st.expander("📝 הוסף הערה לנציג ביום מסוים"):
            c1, c2, c3, c4 = st.columns(4)
            note_agent = c1.selectbox("נציג", df["שם"].tolist())
            note_day   = c2.selectbox("יום",  DAYS_ORDER)
            note_text  = c3.text_input("הערה")
            if c4.button("הוסף"):
                st.session_state.cell_notes[f"{note_agent}_{note_day}"] = note_text
                st.rerun()

        st.divider()
        st.markdown("### 📊 סיכום משמרות")
        summary_rows = []
        for _, row in df.iterrows():
            summary_rows.append({
                "נציג":    row["שם"],
                "☀️ בוקר": sum(1 for d in DAYS_ORDER if row[d] == "בוקר"),
                "🌤 ערב":  sum(1 for d in DAYS_ORDER if row[d] == "ערב"),
                "🌙 לילה": sum(1 for d in DAYS_ORDER if row[d] == "לילה"),
                "סה״כ":   row["סה״כ"],
            })
        st.dataframe(pd.DataFrame(summary_rows).set_index("נציג"), use_container_width=True)

        # ── מד הוגנות ──
        st.divider()
        st.markdown("### ⚖️ מד הוגנות")

        # חישוב סטיית תקן של אחוז המילוי לכל נציג
        fairness_data = []
        for _, row in df.iterrows():
            ag_obj = next((a for a in st.session_state.agents if a["name"]==row["שם"]), {})
            ag_total = ag_obj.get("total", 0)
            filled = row.get("סה״כ", 0)
            if ag_total > 0:
                fill_pct = (filled / ag_total) * 100
                fairness_data.append({"name": row["שם"], "pct": fill_pct, "filled": filled, "total": ag_total})

        if fairness_data:
            avg_pct = sum(f["pct"] for f in fairness_data) / len(fairness_data)
            variance = sum((f["pct"] - avg_pct) ** 2 for f in fairness_data) / len(fairness_data)
            std_dev = variance ** 0.5

            # ציון הוגנות: 100 = מושלם, 0 = גרוע מאוד
            fairness_score = max(0, min(100, 100 - std_dev * 2))

            # צבע לפי ציון
            if fairness_score >= 85:
                grade_color = "#10b981"
                grade_text  = "מצוין"
                grade_emoji = "🏆"
            elif fairness_score >= 70:
                grade_color = "#f59e0b"
                grade_text  = "טוב"
                grade_emoji = "👍"
            else:
                grade_color = "#ef4444"
                grade_text  = "טעון שיפור"
                grade_emoji = "⚠️"

            # מי הכי עמוס ומי הכי פנוי
            sorted_by_pct = sorted(fairness_data, key=lambda x: x["pct"], reverse=True)
            most_loaded   = sorted_by_pct[0]
            least_loaded  = sorted_by_pct[-1]

            st.markdown(f"""
            <div style='background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
                        border-radius:20px;padding:25px;color:white;
                        box-shadow:0 10px 30px rgba(0,0,0,0.15);'>
                <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:20px;'>
                    <div style='text-align:center;flex:1;min-width:150px;'>
                        <div style='font-size:14px;opacity:0.9;margin-bottom:5px;'>ציון הוגנות</div>
                        <div style='font-size:48px;font-weight:800;line-height:1;'>{fairness_score:.0f}</div>
                        <div style='font-size:13px;opacity:0.85;'>מתוך 100</div>
                    </div>
                    <div style='background:white;color:{grade_color};border-radius:14px;
                                padding:14px 22px;font-weight:800;font-size:18px;text-align:center;
                                box-shadow:0 6px 20px rgba(0,0,0,0.2);'>
                        {grade_emoji} {grade_text}
                    </div>
                    <div style='text-align:center;flex:1;min-width:200px;'>
                        <div style='font-size:13px;opacity:0.9;margin-bottom:8px;'>📊 הכי עמוס</div>
                        <div style='font-weight:700;font-size:16px;'>{most_loaded['name']}</div>
                        <div style='font-size:12px;opacity:0.85;'>{most_loaded['filled']}/{most_loaded['total']} ({most_loaded['pct']:.0f}%)</div>
                    </div>
                    <div style='text-align:center;flex:1;min-width:200px;'>
                        <div style='font-size:13px;opacity:0.9;margin-bottom:8px;'>🌿 הכי פנוי</div>
                        <div style='font-weight:700;font-size:16px;'>{least_loaded['name']}</div>
                        <div style='font-size:12px;opacity:0.85;'>{least_loaded['filled']}/{least_loaded['total']} ({least_loaded['pct']:.0f}%)</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # פס התקדמות
            st.markdown(f"""
            <div style='background:#f0f0f5;border-radius:10px;height:8px;
                        margin:15px 0;overflow:hidden;'>
                <div style='background:linear-gradient(90deg,#ef4444,#f59e0b,#10b981);
                            height:100%;width:{fairness_score}%;border-radius:10px;'></div>
            </div>
            """, unsafe_allow_html=True)
        # ── פרופיל נציג ──
        st.divider()
        st.markdown("### 🔍 פרופיל נציג")
        agent_names = df["שם"].tolist()
        selected_agent = st.selectbox("בחר נציג להצגה", ["— בחר —"] + agent_names,
                                       key="profile_select")

        if selected_agent != "— בחר —":
            agent_row = df[df["שם"] == selected_agent].iloc[0]
            ag_color = AGENT_COLORS.get(selected_agent, "#eee")

            morning_days = [d for d in DAYS_ORDER if agent_row[d] == "בוקר"]
            evening_days = [d for d in DAYS_ORDER if agent_row[d] == "ערב"]
            night_days   = [d for d in DAYS_ORDER if agent_row[d] == "לילה"]
            off_days     = [d for d in DAYS_ORDER if agent_row[d] == "—"]

            profile_html = f"""
            <div style='background:linear-gradient(135deg,{ag_color}40,{ag_color}80);
                        border-radius:20px;padding:24px;
                        box-shadow:0 8px 30px rgba(0,0,0,0.1);'>
                <div style='display:flex;align-items:center;gap:16px;margin-bottom:20px;'>
                    <div style='background:{ag_color};width:60px;height:60px;
                                border-radius:50%;display:flex;align-items:center;
                                justify-content:center;font-size:28px;font-weight:800;
                                color:#3d3d5c;box-shadow:0 4px 15px rgba(0,0,0,0.15);'>
                        {selected_agent[0]}
                    </div>
                    <div>
                        <h2 style='margin:0;color:#3d3d5c;font-weight:800;'>{selected_agent}</h2>
                        <p style='margin:0;color:#666;'>סה״כ {agent_row["סה״כ"]} משמרות השבוע</p>
                    </div>
                </div>
                <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;'>
                    <div style='background:white;padding:14px;border-radius:14px;
                                box-shadow:0 4px 12px rgba(0,0,0,0.05);'>
                        <div style='color:#10b981;font-weight:800;margin-bottom:8px;'>☀️ בוקר ({len(morning_days)})</div>
                        <div style='font-size:13px;color:#555;'>{', '.join(morning_days) if morning_days else '—'}</div>
                    </div>
                    <div style='background:white;padding:14px;border-radius:14px;
                                box-shadow:0 4px 12px rgba(0,0,0,0.05);'>
                        <div style='color:#f59e0b;font-weight:800;margin-bottom:8px;'>🌤 ערב ({len(evening_days)})</div>
                        <div style='font-size:13px;color:#555;'>{', '.join(evening_days) if evening_days else '—'}</div>
                    </div>
                    <div style='background:white;padding:14px;border-radius:14px;
                                box-shadow:0 4px 12px rgba(0,0,0,0.05);'>
                        <div style='color:#8b5cf6;font-weight:800;margin-bottom:8px;'>🌙 לילה ({len(night_days)})</div>
                        <div style='font-size:13px;color:#555;'>{', '.join(night_days) if night_days else '—'}</div>
                    </div>
                    <div style='background:white;padding:14px;border-radius:14px;
                                box-shadow:0 4px 12px rgba(0,0,0,0.05);'>
                        <div style='color:#999;font-weight:800;margin-bottom:8px;'>🏖 חופש ({len(off_days)})</div>
                        <div style='font-size:13px;color:#555;'>{', '.join(off_days) if off_days else '—'}</div>
                    </div>
                </div>
            </div>
            """
            st.markdown(profile_html, unsafe_allow_html=True)
        st.divider()
        st.markdown("### 👤 סטטוס מכסה")
        scols = st.columns(len(st.session_state.agents))
        for i, (_, row) in enumerate(df.iterrows()):
            ag_obj   = next((a for a in st.session_state.agents if a["name"]==row["שם"]), {})
            ag_total = ag_obj.get("total", 0)
            filled   = row.get("סה״כ", 0)
            color    = "#2d6a2d" if filled >= ag_total else "#cc4444"
            ag_color = ag_obj.get("color", "#eee")
            with scols[i]:
                st.markdown(f"""
                <div style='background:{ag_color};border-radius:10px;padding:8px;text-align:center;'>
                    <div style='font-size:11px;font-weight:700;color:#3d3d5c;'>{row['שם']}</div>
                    <div style='font-size:18px;font-weight:700;color:{color};'>{filled}/{ag_total}</div>
                </div>
                """, unsafe_allow_html=True)

        st.divider()
        output = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 הורד סידור כ-CSV", data=output,
                           file_name=f"sidur_{st.session_state.week_label or 'export'}.csv",
                           mime="text/csv")

    else:
        st.markdown("""
        <div style='text-align:center;padding:60px 20px;color:#aaa;direction:rtl;'>
            <div style='font-size:60px;'>📋</div>
            <div style='font-size:20px;margin-top:10px;'>לחץ על "צור סידור אוטומטי" כדי להתחיל</div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown("""
    <h2 style='text-align:center;background:linear-gradient(135deg,#667eea,#764ba2);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;
               background-clip:text;font-weight:800;'>📊 סטטיסטיקות היסטוריות</h2>
    """, unsafe_allow_html=True)

    archive = load_archive()
    if not archive:
        st.info("אין נתונים בארכיון עדיין. שמור סידורים כדי לראות סטטיסטיקות.")
    else:
        all_names = list({r["שם"] for entry in archive for r in entry["schedule"]})
        stats = {n: {"בוקר": 0, "ערב": 0, "לילה": 0} for n in all_names}
        for entry in archive:
            for row in entry["schedule"]:
                name = row["שם"]
                for day in DAYS_ORDER:
                    shift = row.get(day, "—")
                    if shift in stats[name]:
                        stats[name][shift] += 1

        # גרף מודרני
        max_val = max(
            (stats[n][s] for n in all_names for s in ["בוקר","ערב","לילה"]),
            default=1
        ) or 1

        bars_html = ""
        for name in all_names:
            total = sum(stats[name].values())
            bars_html += f"""
            <div style='background:white;border-radius:16px;padding:18px;margin:12px 0;
                        box-shadow:0 4px 20px rgba(0,0,0,0.08);'>
                <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;'>
                    <h3 style='margin:0;color:#3d3d5c;font-weight:700;'>{name}</h3>
                    <div style='background:linear-gradient(135deg,#667eea,#764ba2);color:white;
                                padding:6px 14px;border-radius:20px;font-weight:700;font-size:14px;'>
                        סה״כ: {total}
                    </div>
                </div>
            """
            shift_colors = {
                "בוקר": ("#6ee7b7", "#10b981"),
                "ערב":  ("#f59e0b", "#d97706"),
                "לילה": ("#8b5cf6", "#7c3aed"),
            }
            for shift in ["בוקר", "ערב", "לילה"]:
                value = stats[name][shift]
                width = (value / max_val) * 100
                c1, c2 = shift_colors[shift]
                bars_html += f"""
                <div style='display:flex;align-items:center;margin:6px 0;'>
                    <div style='width:60px;font-weight:600;font-size:13px;color:#555;'>{shift}</div>
                    <div style='flex:1;background:#f0f0f5;height:24px;border-radius:12px;overflow:hidden;margin:0 10px;position:relative;'>
                        <div style='background:linear-gradient(90deg,{c1},{c2});height:100%;
                                    width:{width}%;border-radius:12px;
                                    box-shadow:inset 0 -2px 4px rgba(0,0,0,0.1);
                                    transition:width 0.5s ease;'></div>
                    </div>
                    <div style='width:30px;text-align:center;font-weight:700;color:#3d3d5c;'>{value}</div>
                </div>
                """
            bars_html += "</div>"

        components.html(f"""
        <html><head><style>
            @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;600;700;800&display=swap');
            body {{ font-family:'Heebo',sans-serif; direction:rtl; margin:0; padding:10px; background:#f8f9fc; }}
        </style></head><body>{bars_html}</body></html>
        """, height=len(all_names)*220 + 50, scrolling=True)
# ── דירוג חודשי ──
        st.divider()
        st.markdown("""
        <h2 style='text-align:center;background:linear-gradient(135deg,#f093fb,#f5576c);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                   background-clip:text;font-weight:800;'>🏆 דירוג חודשי - 30 ימים אחרונים</h2>
        """, unsafe_allow_html=True)

        cutoff = datetime.now() - timedelta(days=30)
        recent_stats = {n: {"בוקר": 0, "ערב": 0, "לילה": 0, "סה״כ": 0} for n in all_names}
        for entry in archive:
            try:
                entry_date = datetime.strptime(entry["date"].split()[0], "%d/%m/%Y")
            except Exception:
                continue
            if entry_date < cutoff:
                continue
            for row in entry["schedule"]:
                name = row["שם"]
                if name not in recent_stats:
                    continue
                for day in DAYS_ORDER:
                    shift = row.get(day, "—")
                    if shift in ("בוקר", "ערב", "לילה"):
                        recent_stats[name][shift] += 1
                        recent_stats[name]["סה״כ"] += 1

        def make_ranking(category):
            sorted_list = sorted(recent_stats.items(),
                                  key=lambda x: x[1][category], reverse=True)
            return [(name, stats[category]) for name, stats in sorted_list if stats[category] > 0]

        medals = ["🥇", "🥈", "🥉"]
        category_titles = {
            "סה״כ":  ("👑 מלך המשמרות", "#667eea"),
            "בוקר":  ("☀️ אלוף הבקרים", "#10b981"),
            "ערב":   ("🌤 אלוף הערבים", "#f59e0b"),
            "לילה":  ("🌙 אלוף הלילות", "#8b5cf6"),
        }

        rank_cols = st.columns(4)
        for col, (cat, (title, color)) in zip(rank_cols, category_titles.items()):
            ranking = make_ranking(cat)
            with col:
                html = f"<div style='background:white;border-radius:16px;padding:18px;box-shadow:0 4px 20px rgba(0,0,0,0.08);'><div style='color:{color};font-weight:800;font-size:16px;margin-bottom:12px;text-align:center;'>{title}</div>"
                if not ranking:
                    html += "<div style='color:#aaa;text-align:center;'>אין נתונים</div>"
                else:
                    for i, (name, value) in enumerate(ranking[:5]):
                        medal = medals[i] if i < 3 else f"{i+1}."
                        html += f"<div style='display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid #f0f0f5;'><span style='font-weight:600;color:#3d3d5c;'>{medal} {name}</span><span style='background:{color};color:white;padding:2px 10px;border-radius:12px;font-weight:700;font-size:12px;'>{value}</span></div>"
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)
# ── טבלת 3 סופי שבוע אחרונים ──
        st.divider()
        st.markdown("""
        <h2 style='text-align:center;background:linear-gradient(135deg,#f5576c,#f093fb);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                   background-clip:text;font-weight:800;'>📅 3 סופי שבוע אחרונים</h2>
        """, unsafe_allow_html=True)

        weekend_shifts = [
            ("שישי", "ערב",  "🌤 שישי ערב",  "#f59e0b"),
            ("שישי", "לילה", "🌙 שישי לילה", "#8b5cf6"),
            ("שבת",  "בוקר", "☀️ שבת בוקר",  "#10b981"),
            ("שבת",  "ערב",  "🌤 שבת ערב",   "#f59e0b"),
            ("שבת",  "לילה", "🌙 שבת לילה",  "#8b5cf6"),
        ]

        last_3 = load_archive()[:3]
        if not last_3:
            st.info("אין סידורים שמורים בארכיון.")
        else:
            # בניית HTML של הטבלה
            table_html = """
            <table style='width:100%;border-collapse:separate;border-spacing:6px;margin-top:15px;'>
                <thead><tr>
                    <th style='background:linear-gradient(180deg,#ffffff 0%,#e8e4f8 100%);
                               color:#3d3d5c;padding:12px;border-radius:10px;
                               font-weight:800;text-align:center;'>משמרת</th>
            """
            for entry in last_3:
                table_html += f"""
                <th style='background:linear-gradient(180deg,#ffffff 0%,#e8e4f8 100%);
                           color:#3d3d5c;padding:12px;border-radius:10px;
                           font-weight:800;text-align:center;'>{entry['week']}</th>
                """
            table_html += "</tr></thead><tbody>"

            for day, shift, label, color in weekend_shifts:
                table_html += f"""
                <tr>
                    <td style='background:linear-gradient(135deg,{color}22,{color}44);
                               color:#3d3d5c;padding:14px;border-radius:10px;
                               font-weight:800;text-align:center;border-right:5px solid {color};'>
                        {label}
                    </td>
                """
                for entry in last_3:
                    workers = []
                    for row in entry.get("schedule", []):
                        if row.get(day) == shift:
                            workers.append(row["שם"])
                    workers_str = ", ".join(workers) if workers else "—"
                    table_html += f"""
                    <td style='background:white;padding:14px;border-radius:10px;
                               text-align:center;font-weight:600;color:#3d3d5c;
                               box-shadow:0 2px 8px rgba(0,0,0,0.05);'>
                        {workers_str}
                    </td>
                    """
                table_html += "</tr>"
            table_html += "</tbody></table>"

            components.html(f"""
            <html><head><style>
                @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;600;700;800&display=swap');
                body {{ font-family:'Heebo',sans-serif; direction:rtl; margin:0; padding:10px; background:#f8f9fc; }}
            </style></head><body>{table_html}</body></html>
            """, height=500, scrolling=True)

with tab3:
    st.markdown("""
    <h2 style='text-align:center;background:linear-gradient(135deg,#667eea,#764ba2);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;
               background-clip:text;font-weight:800;'>🔍 השוואת שבועות</h2>
    """, unsafe_allow_html=True)

    archive_data = load_archive()
    if len(archive_data) < 2:
        st.info("צריך לפחות 2 סידורים בארכיון כדי להשוות. שמור עוד סידורים!")
    else:
        week_labels = [e["week"] for e in archive_data]

        col_a, col_b = st.columns(2)
        with col_a:
            week_1 = st.selectbox("בחר שבוע ראשון", week_labels, key="cmp_week1")
        with col_b:
            week_2 = st.selectbox("בחר שבוע שני", week_labels,
                                   index=min(1, len(week_labels)-1), key="cmp_week2")

        entry_1 = next((e for e in archive_data if e["week"] == week_1), None)
        entry_2 = next((e for e in archive_data if e["week"] == week_2), None)

        if entry_1 and entry_2:
            df_1 = archive_to_df(entry_1)
            df_2 = archive_to_df(entry_2)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"#### 📅 {week_1}")
                st.dataframe(df_1, use_container_width=True, height=400)
            with c2:
                st.markdown(f"#### 📅 {week_2}")
                st.dataframe(df_2, use_container_width=True, height=400)

            st.divider()
            st.markdown("### 📊 השוואת משמרות לפי נציג")

            all_names = sorted(set(df_1["שם"].tolist()) | set(df_2["שם"].tolist()))
            cmp_rows = []
            for name in all_names:
                row1 = df_1[df_1["שם"]==name]
                row2 = df_2[df_2["שם"]==name]
                t1 = row1["סה״כ"].values[0] if len(row1) else 0
                t2 = row2["סה״כ"].values[0] if len(row2) else 0
                diff = t2 - t1
                arrow = "↑" if diff > 0 else ("↓" if diff < 0 else "=")
                cmp_rows.append({
                    "נציג": name,
                    f"שבוע {week_1}": t1,
                    f"שבוע {week_2}": t2,
                    "שינוי": f"{arrow} {abs(diff)}" if diff else "= 0"
                })
            st.dataframe(pd.DataFrame(cmp_rows).set_index("נציג"), use_container_width=True)

with tab4:
    st.markdown("""
    <h2 style='text-align:center;background:linear-gradient(135deg,#667eea,#764ba2);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;
               background-clip:text;font-weight:800;'>🗂 ארכיון סידורים</h2>
    """, unsafe_allow_html=True)

    archive = load_archive()
    if not archive:
        st.info("אין סידורים שמורים עדיין.")
    else:
        # חיפוש
        search = st.text_input("🔍 חפש בארכיון", placeholder="שם נציג, תאריך, או מילת מפתח...")

        filtered = []
        for entry in archive:
            if not search:
                filtered.append(entry)
                continue
            search_lower = search.lower()
            # חיפוש בשבוע, תאריך, הערות
            if (search_lower in entry.get("week", "").lower() or
                search_lower in entry.get("date", "").lower() or
                search_lower in entry.get("notes", "").lower()):
                filtered.append(entry)
                continue
            # חיפוש בשמות נציגים
            for row in entry.get("schedule", []):
                if search_lower in row.get("שם", "").lower():
                    filtered.append(entry)
                    break

        if search and not filtered:
            st.warning(f"לא נמצאו תוצאות עבור '{search}'")
        elif search:
            st.success(f"נמצאו {len(filtered)} תוצאות")

        for entry in filtered:
            with st.expander(f"📅 {entry['week']}  |  {entry['date']}"):
                if entry.get("notes"):
                    st.markdown(f"📝 {entry['notes']}")
                arc_df = archive_to_df(entry)
                st.dataframe(arc_df, use_container_width=True)
                c1, c2 = st.columns(2)
                with c1:
                    output = arc_df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button("📥 הורד CSV", data=output,
                                       file_name=f"sidur_{entry['week']}.csv",
                                       mime="text/csv", key=f"dl_{entry['week']}")
                with c2:
                    if st.button("🗑 מחק", key=f"del_{entry['week']}"):
                        delete_from_archive(entry["week"])
                        st.rerun()
