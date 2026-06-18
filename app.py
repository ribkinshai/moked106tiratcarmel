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
            pref_map = {
                a["name"]: {
                    "בוקר": a.get("pref_morning", []),
                    "ערב":  a.get("pref_evening", []),
                    "לילה": a.get("pref_night",   []),
                }
                for a in st.session_state.agents
            }
            with st.spinner("מחשב סידור..."):
                df = generate_schedule(
                    st.session_state.agents, DAYS_ORDER,
                    is_fourth_saturday=st.session_state.fourth_saturday,
                    day_off=day_off_map,
                    twelve_hour=st.session_state.twelve_hour,
                    pref_days=pref_map,
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

        # הצג טבלה כרגיל
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
                        f"padding:3px 8px;display:inline-block;margin:2px;"
                        f"font-size:12px;font-weight:600'>"
                        f"{ag}{watcher_badge}{hours_display}</span>"
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
                                st.session_state.twelve_hour[key_12] = checked

                            # שינוי נציג רואה
                            if st.button("👁 רואה", key=f"watch_{ag}_{day}_{shift}"):
                                st.session_state.watcher[watcher_key] = ag
                                st.rerun()

                    # הוספת נציג
                    with cols[len(agents_in)+1]:
                        if free_agents:
                            add = st.selectbox("➕", ["—"]+free_agents,
                                               key=f"add_{day}_{shift}",
                                               label_visibility="collapsed")
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
