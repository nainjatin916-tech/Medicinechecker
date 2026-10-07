"""
MediSafe - 6. Smart Medicine Reminders
Schedule medication alerts, manage daily reminders, and log dose adherence
with instant 'Mark Taken' and 'Mark Skipped' actions.
"""

from datetime import date, timedelta
import streamlit as st
from config import (
    APP_NAME,
    FREQUENCIES,
    DOSE_TAKEN,
    DOSE_SKIPPED,
)
from database import init_database
from medicine import get_all_medicines
from reminder import (
    create_reminder,
    get_all_reminders,
    delete_reminder,
    get_today_doses,
    mark_dose_status,
)
from utils import (
    render_header,
    render_academic_disclaimer,
    get_status_badge_html,
    render_empty_state,
    render_viva_note,
)

st.set_page_config(
    page_title=f"{APP_NAME} - Reminders & Doses",
    page_icon="⏰",
    layout="wide",
)

init_database()
render_header("Smart Medicine Reminders", "Configure recurring medication dosage schedules and track daily intake compliance")

rem_tab1, rem_tab2 = st.tabs([
    "📅 Today's Doses & Compliance",
    "➕ Create & Manage Reminders",
])

# 1. TODAY'S DOSES & COMPLIANCE
with rem_tab1:
    st.markdown("### 💊 Today's Medication Schedule")
    st.caption("Active scheduled doses for today. Mark items as 'Taken' or 'Skipped' to build an accurate medication history.")

    today_doses = get_today_doses()
    if today_doses:
        for dose in today_doses:
            c1, c2, c3, c4 = st.columns([3, 2, 2, 3])
            with c1:
                st.markdown(f"**💊 {dose['medicine_name']}**")
                st.caption(f"Dosage: {dose['dosage']} | Mfr: {dose['manufacturer']}")
            with c2:
                time_only = dose['scheduled_time'].split(' ')[1][:5]
                st.markdown(f"**Scheduled:** `{time_only}`")
                if dose['actual_time']:
                    st.caption(f"Logged at: {dose['actual_time']}")
            with c3:
                badge = get_status_badge_html(dose['status'])
                st.markdown(badge, unsafe_allow_html=True)
            with c4:
                if dose['status'] == "PENDING":
                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        if st.button("Mark Taken", key=f"rem_page_taken_{dose['history_id']}", use_container_width=True):
                            mark_dose_status(dose['history_id'], DOSE_TAKEN, "Taken as scheduled")
                            st.rerun()
                    with btn_c2:
                        if st.button("Mark Skipped", key=f"rem_page_skip_{dose['history_id']}", use_container_width=True):
                            mark_dose_status(dose['history_id'], DOSE_SKIPPED, "Skipped by user")
                            st.rerun()
                else:
                    st.caption(f"Status recorded: **{dose['status']}**")
                    with st.popover("Change Status"):
                        if st.button("Reset to PENDING", key=f"reset_{dose['history_id']}"):
                            mark_dose_status(dose['history_id'], "PENDING", "")
                            st.rerun()
            st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
    else:
        render_empty_state("No Medication Doses Scheduled for Today", "Configure a daily routine in the Create Reminder tab to populate today's checklist.", icon="🕒")

# 2. CREATE & MANAGE REMINDERS
with rem_tab2:
    col_add, col_list = st.columns([1, 1])

    with col_add:
        st.markdown("### ➕ Create New Reminder")
        all_meds = get_all_medicines()

        if not all_meds:
            st.warning("Please add at least one medicine to the inventory first.")
        else:
            with st.form("create_reminder_form"):
                selected_med = st.selectbox(
                    "Select Medicine *",
                    options=all_meds,
                    format_func=lambda m: f"{m['medicine_name']} ({m['dosage']})",
                )
                rem_dosage = st.text_input("Dosage Instructions *", value=selected_med["dosage"])
                rem_time = st.time_input("Reminder Time *")
                rem_frequency = st.selectbox("Frequency *", options=FREQUENCIES, index=1)
                
                today = date.today()
                c_sdate, c_edate = st.columns(2)
                with c_sdate:
                    start_d = st.date_input("Start Date *", value=today)
                with c_edate:
                    end_d = st.date_input("End Date *", value=today + timedelta(days=30))

                submitted = st.form_submit_button("Create Reminder Schedule", type="primary", use_container_width=True)
                if submitted:
                    time_str = rem_time.strftime("%H:%M")
                    success, msg, r_id = create_reminder(
                        medicine_id=selected_med["id"],
                        dosage=rem_dosage,
                        reminder_time=time_str,
                        frequency=rem_frequency,
                        start_date=str(start_d),
                        end_date=str(end_d),
                    )
                    if success:
                        st.success(f"✅ Reminder schedule created! (ID: {r_id})")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed: {msg}")

    with col_list:
        st.markdown("### 📋 Active Reminders")
        active_reminders = get_all_reminders()
        if active_reminders:
            for r in active_reminders:
                with st.container():
                    st.markdown(f"**🔔 {r['medicine_name']}** — `{r['reminder_time']}` ({r['frequency']})")
                    st.caption(f"Dosage: {r['dosage']} | Period: {r['start_date']} to {r['end_date']}")
                    if st.button("🗑️ Delete Schedule", key=f"del_rem_{r['id']}"):
                        delete_reminder(r["id"])
                        st.success("Deleted schedule.")
                        st.rerun()
                    st.markdown("<hr style='margin: 8px 0;'>", unsafe_allow_html=True)
        else:
            render_empty_state("No Active Reminders Found", "Use the creation form on the left to set up a recurring medication reminder.", icon="🔔")

with st.expander("🎓 Examiner Viva Information: Idempotent Dose Slot Generation"):
    render_viva_note(
        "Preventing Duplicate Medication Slots",
        "• <b>Composite Unique Key</b>: <code>UNIQUE(medicine_id, scheduled_time)</code> prevents generating duplicate dose-history records even if the page refreshes multiple times.<br>"
        "• <b>Idempotent Inserts</b>: Uses <code>INSERT OR IGNORE</code> when computing today's active dose occurrences.<br>"
        "• <b>Audit Integrity</b>: Dose status transitions (Taken / Skipped) record actual wall-clock execution timestamps while preserving original scheduled times.",
    )

render_academic_disclaimer()
