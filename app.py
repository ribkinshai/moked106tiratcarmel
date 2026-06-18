import streamlit as st
import pandas as pd
from scheduler import generate_schedule

st.set_page_config(
    page_title="סידור עבודה – מוקד 106",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(table_html, unsafe_allow_html=True)
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Heebo', sans-serif; direction: rtl; }
    .main { background-color: #f8f9fc; }
    h1, h2, h3 { color: #3d3d5c; }

    .badge { display:inline-block; padding:3px 12px; border-radius:20px; font-size:13px; font-weight:600; margin:2px; }
    .badge-morning { background:#d4ecd4; color:#2d6a2d; }
    .badge-noon    { background:#fde8c8; color:#7a4a00; }
    .badge-night   { background:#d9d4f0; color:#3a2070; }

    .schedule-table { width:100%; border-collapse:collapse; direction:rtl; }
    .schedule-table th {
        background:#e8e4f8; color:#3d3d5c; padding:10px 8px;
        text-align:center; font-weight:700; font-size:15px; border:1px solid #ccc9e0;
    }
    .schedule-table td {
        padding:10px 8px; text-align:center; border:1px solid #ddd;
        font-size:13px; vertical-align:top; min-width:100px;
    }
    .schedule-table tr:hover td { background-color: inherit; }

    .cell-morning { background:#d4ecd4 !important; color:#2d6a2d; }
    .cell-noon    { background:#fde8c8 !important; color:#7a4a00; }
    .cell-night   { background:#d9d4f0 !important; color:#3a2070; }

    div[data-testid="stSidebar"] { background:#edeaf8; }
    .stButton > button {
        background:#7c6fc4; color:white; border-radius:10px;
        border:none; font-family:'Heebo',sans-serif; font-weight:600;
    }
    .stButton > button:hover { background:#5c4fa4; }
</style>
""", unsafe_allow_html=True)

# ─── Session State ────────────────────────────────────────────────────────────
if "agents" not in st.session_state:
    st.session_state.agents = [
        {"name": "לב",     "total": 5, "pref": "לילה"},
        {"name": "איתי",   "total": 5, "pref": "לילה"},
        {"name": "גיא",    "total": 5, "pref": "לילה"},
        {"name": "אלינור", "total": 5, "pref": "לילה"},
        {"name": "שרית",   "total": 5, "pref": "בוקר/ערב"},
        {"name": "רונית",  "total": 5, "pref": "בוקר/ערב"},
        {"name": "שני",    "total": 5, "pref": "בוקר/ערב"},
        {"name": "נציג 8", "total": 4, "pref": "ללא העדפה"},
        {"name": "נציג 9", "total": 4, "pref": "ללא העדפה"},
        {"name": "נציג 10","total": 4, "pref": "ללא העדפה"},
    ]

if "schedule_df" not in st.session_state:
    st.session_state.schedule_df = None

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

DAYS_ORDER    = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
SHIFTS        = ["בוקר", "ערב", "לילה"]
SHIFT_OPTIONS = ["בוקר", "ערב", "לילה", "—"]
PREF_OPTIONS  = ["לילה", "בוקר/ערב", "ללא העדפה"]

SHIFT_HOURS = {
    "בוקר": "07:00-15:00",
    "ערב":  "15:00-23:00",
    "לילה": "23:00-07:00",
}
SHIFT_CLASS = {"בוקר": "cell-morning", "ערב": "cell-noon", "לילה": "cell-night"}
SHIFT_EMOJI = {"בוקר": "☀️", "ערב": "🌤", "לילה": "🌙"}

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 👥 ניהול נציגים")
    updated_agents = []
    for i, agent in enumerate(st.session_state.agents):
        with st.expander(f"✏️ {agent['name']}", expanded=False):
            name  = st.text_input("שם", value=agent["name"], key=f"name_{i}")
            total = st.number_input("מכסה שבועית", min_value=1, max_value=7,
                                    value=agent["total"], key=f"total_{i}")
            pref  = st.selectbox("העדפת משמרת", PREF_OPTIONS,
                                  index=PREF_OPTIONS.index(agent["pref"]), key=f"pref_{i}")
            updated_agents.append({"name": name, "total": total, "pref": pref})
    st.session_state.agents = updated_agents

    st.divider()
    if st.button("➕ הוסף נציג"):
        st.session_state.agents.append({"name": f"נציג {len(st.session_state.agents)+1}",
                                         "total": 4, "pref": "ללא העדפה"})
        st.rerun()
    if len(st.session_state.agents) > 1:
        if st.button("🗑 הסר נציג אחרון"):
            st.session_state.agents.pop()
            st.rerun()

    st.divider()
    st.markdown("**מקרא צבעים:**")
    st.markdown("""
    <span class='badge badge-morning'>☀️ בוקר 07:00-15:00</span><br><br>
    <span class='badge badge-noon'>🌤 ערב 15:00-23:00</span><br><br>
    <span class='badge badge-night'>🌙 לילה 23:00-07:00</span>
    """, unsafe_allow_html=True)

# ─── Main ─────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='text-align:right'>📋 סידור עבודה – מוקד 106</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:right; color:#888;'>שיבוץ אוטומטי חכם עם עריכה ידנית</p>",
            unsafe_allow_html=True)

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    if st.button("⚡ צור סידור אוטומטי", use_container_width=True):
        with st.spinner("מחשב סידור אופטימלי..."):
            df = generate_schedule(st.session_state.agents, DAYS_ORDER)
            st.session_state.schedule_df = df
            st.session_state.edit_mode = False
        st.success("הסידור נוצר בהצלחה! ✅")

with col2:
    if st.session_state.schedule_df is not None:
        if st.button("✏️ מצב עריכה", use_container_width=True):
            st.session_state.edit_mode = not st.session_state.edit_mode

with col3:
    if st.session_state.schedule_df is not None:
        if st.button("🔄 אפס", use_container_width=True):
            st.session_state.schedule_df = None
            st.session_state.edit_mode = False
            st.rerun()

# ─── Display ──────────────────────────────────────────────────────────────────
if st.session_state.schedule_df is not None:
    df = st.session_state.schedule_df

    # ── מצב עריכה ──
    if st.session_state.edit_mode:
        st.markdown("### ✏️ עריכה ידנית")
        st.info("שנה משמרות ישירות בטבלה למטה, ולחץ 'שמור שינויים' בסיום.")

        edited_data = {}
        for idx, row in df.iterrows():
            agent_name = row["שם"]
            edited_data[agent_name] = {"שם": agent_name}
            cols = st.columns([2] + [1]*7)
            cols[0].markdown(f"**{agent_name}**")
            for j, day in enumerate(DAYS_ORDER):
                current_val = row[day]
                options_idx = SHIFT_OPTIONS.index(current_val) if current_val in SHIFT_OPTIONS else 3
                sel = cols[j+1].selectbox(
                    day, SHIFT_OPTIONS,
                    index=options_idx,
                    key=f"edit_{agent_name}_{day}",
                    label_visibility="collapsed"
                )
                edited_data[agent_name][day] = sel

        if st.button("💾 שמור שינויים", type="primary"):
            new_df = pd.DataFrame(list(edited_data.values()))
            new_df["סה״כ"] = new_df[DAYS_ORDER].apply(
                lambda r: sum(1 for v in r if v != "—"), axis=1)
            st.session_state.schedule_df = new_df
            st.session_state.edit_mode = False
            st.success("השינויים נשמרו! ✅")
            st.rerun()

    # ── מצב תצוגה ──
    else:
        st.markdown("### 📅 סידור השבוע")

        # כותרות – ימים
        header_html = "".join(f"<th>{day}</th>" for day in DAYS_ORDER)

        rows_html = ""
        for shift in SHIFTS:
            shift_class = SHIFT_CLASS[shift]
            emoji = SHIFT_EMOJI[shift]
            hours = SHIFT_HOURS[shift]

            rows_html += "<tr>"
            for day in DAYS_ORDER:
                agents_in_shift = df[df[day] == shift]["שם"].tolist()
                agents_str = "<br>".join(agents_in_shift) if agents_in_shift else "—"
                rows_html += f"""
                <td class='{shift_class}'>
                    <div style='font-weight:700; margin-bottom:4px;'>{emoji} {shift}</div>
                    <div style='font-size:11px; margin-bottom:6px; opacity:0.8;'>{hours}</div>
                    <div style='font-size:13px; line-height:1.8;'>{agents_str}</div>
                </td>
                """
            rows_html += "</tr>"

        table_html = f"""
        <div style='overflow-x:auto; direction:rtl;'>
        <table class='schedule-table'>
            <thead><tr>{header_html}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        </div>
        """
        st.markdown(table_html, unsafe_allow_html=True)

        # ── סיכום נציגים ──
        st.divider()
        st.markdown("### 📊 סיכום משמרות לנציג")
        summary_cols = st.columns(len(st.session_state.agents))
        for i, (_, row) in enumerate(df.iterrows()):
            agent_total = next((a["total"] for a in st.session_state.agents if a["name"] == row["שם"]), 0)
            filled = row.get("סה״כ", 0)
            with summary_cols[i]:
                color = "#2d6a2d" if filled >= agent_total else "#cc4444"
                st.markdown(f"""
                <div style='background:white; border-radius:10px; padding:10px;
                            box-shadow:0 2px 6px rgba(0,0,0,0.07); text-align:center; direction:rtl;'>
                    <div style='font-size:13px; font-weight:700; color:#3d3d5c;'>{row['שם']}</div>
                    <div style='font-size:22px; font-weight:700; color:{color};'>{filled}/{agent_total}</div>
                    <div style='font-size:11px; color:#888;'>משמרות</div>
                </div>
                """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style='text-align:center; padding:60px 20px; color:#aaa; direction:rtl;'>
        <div style='font-size:60px;'>📋</div>
        <div style='font-size:20px; margin-top:10px;'>לחץ על "צור סידור אוטומטי" כדי להתחיל</div>
    </div>
    """, unsafe_allow_html=True)
