import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from scheduler import generate_schedule, AGENT_COLORS, SHIFT_HOURS, DAYS_ORDER, SHIFTS, NO_12_HOUR
from archive import load_archive, save_to_archive, delete_from_archive, archive_to_df

st.set_page_config(
    page_title="סידור עבודה – מוקד 106",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Heebo', sans-serif; direction: rtl; }
    .main { background-color: #f8f9fc; }
    div[data-testid="stSidebar"] { background:#edeaf8; }
    .stButton > button {
        background:#7c6fc4; color:white; border-radius:10px;
        border:none; font-family:'Heebo',sans-serif; font-weight:600;
    }
    .stButton > button:hover { background:#5c4fa4; }
    .alert-box {
        background:#fff3cd; border:1px solid #ffc107; border-radius:8px;
        padding:10px 16px; margin:8px 0; color:#856404; direction:rtl;
    }
</style>
""", unsafe_allow_html=True)

if "agents" not in st.session_state:
    st.session_state.agents = [
        {"name": "לב",    "total": 5, "pref": "לילה",     "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("לב","#ccc")},
        {"name": "איתי",  "total": 3, "pref": "לילה",     "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("איתי","#ccc")},
        {"name": "גיא",   "total": 5, "pref": "לילה",     "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("גיא","#ccc")},
        {"name": "אלינור","total": 2, "pref": "לילה",     "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("אלינור","#ccc")},
        {"name": "שרית",  "total": 5, "pref": "בוקר/ערב", "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("שרית","#ccc")},
        {"name": "רונית", "total": 5, "pref": "פיזור",    "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("רונית","#ccc")},
        {"name": "שני",   "total": 5, "pref": "פיזור",    "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("שני","#ccc")},
        {"name": "ריקי",  "total": 3, "pref": "בוקר",     "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("ריקי","#ccc")},
        {"name": "אדיר",  "total": 5, "pref": "ללא העדפה","status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("אדיר","#ccc")},
        {"name": "טלי",   "total": 5, "pref": "ללא העדפה","status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("טלי","#ccc")},
        {"name": "סימה",  "total": 2, "pref": "ערב",      "status": "פעיל", "day_off": [], "color": AGENT_COLORS.get("סימה","#ccc")},
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

SHIFT_CLASS  = {"בוקר": "cell-morning", "ערב": "cell-noon", "לילה": "cell-night"}
SHIFT_EMOJI  = {"בוקר": "☀️", "ערב": "🌤", "לילה": "🌙"}
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
            updated_agents.append({
                **agent,
                "status": status, "total": total, "day_off": day_off,
                "pref_morning": pref_morning,
                "pref_evening": pref_evening,
                "pref_night":   pref_night,
            })
    st.session_state.agents = updated_agents

    st.divider()
    st.markdown("**מקרא:**")
    st.markdown("🟢 בוקר 07:00-15:00")
    st.markdown("🔵 בוקר 12ש 07:00-19:00")
    st.markdown("🟡 ערב 15:00-23:00")
    st.markdown("🟣 לילה 23:00-07:00")
    st.markdown("🔴 לילה 12ש 19:00-07:00")

tab1, tab2, tab3 = st.tabs(["📋 סידור", "📊 סטטיסטיקות", "🗂 ארכיון"])

with tab1:
    st.markdown("<h1 style='text-align:right'>📋 סידור עבודה – מוקד 106</h1>",
                unsafe_allow_html=True)
    if st.session_state.week_label:
        st.markdown(f"**שבוע:** {st.session_state.week_label}")
    if st.session_state.week_notes:
        st.markdown(f"📝 {st.session_state.week_notes}")

    col1, col2, col3, col4 = st.columns([2,1,1,1])
    with col1:
        if st.button("⚡ צור סידור אוטומטי", use_container_width=True):
        day_off_map = {a["name"]: a.get("day_off",[]) for a in st.session_state.agents}
        with st.spinner("מחשב סידור..."):
            df = generate_schedule(
                st.session_state.agents, DAYS_ORDER,
                is_fourth_saturday=st.session_state.fourth_saturday,
                day_off=day_off_map,
                twelve_hour=st.session_state.twelve_hour,
            )
            st.session_state.schedule_df = df
            st.session_state.edit_mode   = False
        st.success("הסידור נוצר! ✅")
        st.write("ראשון בוקר:", df[df["ראשון"] == "בוקר"]["שם"].tolist())
        st.write("ראשון לילה:", df[df["ראשון"] == "לילה"]["שם"].tolist())
        st.write("שבת לילה:", df[df["שבת"] == "לילה"]["שם"].tolist())
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
                        and st.session_state.twelve_hour.get(n, False)
                        and n not in NO_12_HOUR
                    )
                    required = max(0, required - twelve_count)
                if count < required:
                    alerts.append(f"⚠️ {day} – {shift}: {count}/{required} נציגים")
        if alerts:
            st.markdown("### ⚠️ התראות")
            for a in alerts:
                st.markdown(f"<div class='alert-box'>{a}</div>", unsafe_allow_html=True)

    if st.session_state.schedule_df is not None and st.session_state.edit_mode:
        st.markdown("### ✏️ עריכה ידנית")
        df = st.session_state.schedule_df

        header_cols = st.columns([1.5] + [1]*7 + [0.8])
        header_cols[0].markdown("**נציג**")
        for j, day in enumerate(DAYS_ORDER):
            header_cols[j+1].markdown(f"**{day}**")
        header_cols[8].markdown("**12ש**")

        edited_data = {}
        for idx, row in df.iterrows():
            agent_name = row["שם"]
            edited_data[agent_name] = {"שם": agent_name}
            ag_color = AGENT_COLORS.get(agent_name, "#eee")
            cols = st.columns([1.5] + [1]*7 + [0.8])
            cols[0].markdown(
                f"<span style='background:{ag_color};padding:3px 8px;"
                f"border-radius:6px;font-weight:700'>{agent_name}</span>",
                unsafe_allow_html=True)
            has_morning_night = False
            for j, day in enumerate(DAYS_ORDER):
                current_val = row[day]
                opt_idx = SHIFT_OPTIONS.index(current_val) if current_val in SHIFT_OPTIONS else 3
                sel = cols[j+1].selectbox("", SHIFT_OPTIONS, index=opt_idx,
                                           key=f"edit_{agent_name}_{day}",
                                           label_visibility="collapsed")
                edited_data[agent_name][day] = sel
                if sel in ("בוקר", "לילה"):
                    has_morning_night = True

            can_12 = agent_name not in NO_12_HOUR and has_morning_night
            if can_12:
                tw = cols[8].checkbox("", value=st.session_state.twelve_hour.get(agent_name, False),
                                       key=f"12h_{agent_name}")
                st.session_state.twelve_hour[agent_name] = tw
            else:
                cols[8].markdown("—")

        st.divider()
        st.markdown("### 👁 נציג רואה")
        for shift in SHIFTS:
            st.markdown(f"**{SHIFT_EMOJI[shift]} {shift}**")
            watch_cols = st.columns(7)
            for j, day in enumerate(DAYS_ORDER):
                key       = f"{day}_{shift}"
                agents_in = ["—"] + df[df[day] == shift]["שם"].tolist()
                current   = st.session_state.watcher.get(key, "—")
                idx_val   = agents_in.index(current) if current in agents_in else 0
                chosen    = watch_cols[j].selectbox(day, agents_in, index=idx_val,
                                                     key=f"watch_{key}")
                st.session_state.watcher[key] = chosen

        if st.button("💾 שמור שינויים", type="primary"):
            new_df = pd.DataFrame(list(edited_data.values()))
            new_df["סה״כ"] = new_df[DAYS_ORDER].apply(
                lambda r: sum(1 for v in r if v != "—"), axis=1)
            st.session_state.schedule_df = new_df
            st.session_state.edit_mode   = False
            st.success("נשמר! ✅")
            st.rerun()

    elif st.session_state.schedule_df is not None:
        df     = st.session_state.schedule_df
        twelve = st.session_state.twelve_hour

        header_html = "".join(f"<th>{day}</th>" for day in DAYS_ORDER)
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
                    if twelve.get(ag) and ag not in NO_12_HOUR:
                        if shift == "בוקר":
                            display_hours = "07:00-19:00"
                        elif shift == "לילה":
                            display_hours = "19:00-07:00"
                        else:
                            display_hours = hours
                    else:
                        display_hours = hours
                    watcher_key   = f"{day}_{shift}"
                    is_watcher    = st.session_state.watcher.get(watcher_key) == ag
                    watcher_badge = " 👁" if is_watcher else ""
                    cells.append(
                        f"<span style='background:{color};border-radius:6px;"
                        f"padding:3px 8px;display:inline-block;margin:2px;"
                        f"font-size:12px;font-weight:600'>"
                        f"{ag}{watcher_badge}<br>"
                        f"<span style='font-weight:400;font-size:11px'>{display_hours}</span>"
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
            body {{ font-family:'Heebo',sans-serif; direction:rtl; margin:0; }}
            table {{ width:100%; border-collapse:collapse; }}
            th {{ background:#e8e4f8; color:#3d3d5c; padding:10px;
                  text-align:center; font-size:14px; border:1px solid #ccc9e0; }}
            td {{ padding:10px; text-align:center; border:1px solid #ddd;
                  vertical-align:top; min-width:110px; line-height:1.8; }}
            .cell-morning {{ background:#d4ecd4; color:#2d6a2d; }}
            .cell-noon    {{ background:#fde8c8; color:#7a4a00; }}
            .cell-night   {{ background:#d9d4f0; color:#3a2070; }}
            small {{ font-size:11px; }}
        </style></head><body>
        <table>
            <thead><tr>{header_html}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        </body></html>
        """
        components.html(full_html, height=440, scrolling=True)

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
    st.markdown("### 📊 סטטיסטיקות היסטוריות")
    archive = load_archive()
    if not archive:
        st.info("אין נתונים בארכיון עדיין.")
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
        chart_data = pd.DataFrame(stats).T
        chart_data.index.name = "נציג"
        st.bar_chart(chart_data)

with tab3:
    st.markdown("### 🗂 ארכיון סידורים")
    archive = load_archive()
    if not archive:
        st.info("אין סידורים שמורים עדיין.")
    else:
        for entry in archive:
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
