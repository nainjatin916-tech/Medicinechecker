"""
MediSafe - 7. Medication Dose History & Compliance Reports
Audit logs of past doses, adherence statistics, compliance calculation,
and historical CSV export.
"""

import streamlit as st
import pandas as pd
from config import (
    APP_NAME,
    DOSE_TAKEN,
    DOSE_SKIPPED,
    DOSE_PENDING,
)
from database import init_database
from medicine import get_all_medicines
from reminder import get_medication_history
from utils import (
    render_header,
    render_academic_disclaimer,
    render_metric_card,
    get_status_badge_html,
    render_empty_state,
    render_viva_note,
)

st.set_page_config(
    page_title=f"{APP_NAME} - Dose History",
    page_icon="📜",
    layout="wide",
)

init_database()
render_header("Medication History & Adherence", "Historical log of taken, skipped, and pending medication doses")

# Filter controls
col_status, col_med, col_export = st.columns([2, 3, 2])

all_meds = get_all_medicines()
med_options = {0: "All Medicines"}
for m in all_meds:
    med_options[m["id"]] = m["medicine_name"]

with col_status:
    status_filter = st.selectbox("Status Filter", options=["ALL", DOSE_TAKEN, DOSE_SKIPPED, DOSE_PENDING], index=0)

with col_med:
    selected_med_id = st.selectbox("Filter by Medicine", options=list(med_options.keys()), format_func=lambda x: med_options[x], index=0)

history_records = get_medication_history(
    status_filter=status_filter,
    medicine_filter=selected_med_id if selected_med_id != 0 else None,
    limit=200,
)

# Adherence metrics calculation
all_history = get_medication_history(status_filter="ALL", limit=500)
total_logged = len(all_history)
taken_count = sum(1 for h in all_history if h["status"] == DOSE_TAKEN)
skipped_count = sum(1 for h in all_history if h["status"] == DOSE_SKIPPED)
pending_count = sum(1 for h in all_history if h["status"] == DOSE_PENDING)

completed_count = taken_count + skipped_count
adherence_rate = (taken_count / completed_count * 100) if completed_count > 0 else 0.0

with col_export:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    if history_records:
        df_export = pd.DataFrame(history_records)
        csv_data = df_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export History (CSV)",
            data=csv_data,
            file_name="medisafe_dose_history.csv",
            mime="text/csv",
            use_container_width=True,
        )

# Metric Summary Cards
st.markdown("### 📊 Adherence & Intake Summary")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.markdown(render_metric_card("Compliance Rate", f"{adherence_rate:.1f}%", f"{taken_count} of {completed_count} completed", "#10B981", "📈"), unsafe_allow_html=True)
with kpi2:
    st.markdown(render_metric_card("Total Doses Taken", taken_count, "Successfully logged", "#059669", "✔️"), unsafe_allow_html=True)
with kpi3:
    st.markdown(render_metric_card("Total Doses Skipped", skipped_count, "Intentionally skipped", "#64748B", "⏭️"), unsafe_allow_html=True)
with kpi4:
    st.markdown(render_metric_card("Pending Doses", pending_count, "Awaiting intake confirmation", "#F59E0B", "🕒"), unsafe_allow_html=True)

st.divider()

# History Table
st.markdown("### 📋 Historical Dose Audit Log")
if not history_records:
    render_empty_state("No Medication Dose History Found", "No recorded intake occurrences match the active filter criteria.", icon="📜")
else:
    # Table layout
    display_rows = []
    for h in history_records:
        display_rows.append({
            "Medicine": h["medicine_name"],
            "Dosage": h["dosage"],
            "Scheduled Time": h["scheduled_time"],
            "Actual Time": h["actual_time"] or "—",
            "Status": h["status"],
            "Manufacturer": h["manufacturer"],
            "Batch": h["batch_number"],
            "Notes": h["notes"] or "",
        })
    df_display = pd.DataFrame(display_rows)
    st.dataframe(df_display, use_container_width=True, hide_index=True)

with st.expander("🎓 Examiner Viva Information: Adherence Metric Computation"):
    render_viva_note(
        "Adherence Rate Formula",
        "• <b>Formula</b>: <code>Adherence = [Total Taken / (Total Taken + Total Skipped)] * 100</code>.<br>"
        "• <b>Pending Exclusion</b>: Unfulfilled future doses are excluded from completed calculations to prevent false-negative compliance skew.<br>"
        "• <b>CSV Compliance Export</b>: Supports downloading audit-grade records for doctor review or academic evaluation.",
    )

render_academic_disclaimer()
