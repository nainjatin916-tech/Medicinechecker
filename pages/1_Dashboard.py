"""
MediSafe - 1. Dashboard Page
Interactive overview featuring 7 summary KPI cards, Priority Safety Alerts,
Today's upcoming dose schedules with quick action buttons, and Plotly analytics charts.
"""

import streamlit as st
from config import APP_NAME, APP_SUBTITLE, APP_TAGLINE, DEFAULT_EXPIRING_SOON_DAYS, DOSE_TAKEN, DOSE_SKIPPED
from database import init_database
from medicine import get_all_medicines
from reminder import get_today_doses, mark_dose_status
from notification import get_active_alerts
from dashboard import (
    get_dashboard_summary_metrics,
    create_status_distribution_chart,
    create_dose_history_chart,
    create_manufacturer_chart,
    create_upcoming_expiry_timeline,
)
from utils import (
    render_header,
    render_academic_disclaimer,
    render_metric_card,
    get_status_badge_html,
    render_empty_state,
    render_viva_note,
)

# Page configuration
st.set_page_config(
    page_title=f"{APP_NAME} - Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ensure database is initialized
init_database()

# Header
render_header(
    title="MEDISAFE",
    subtitle="Medicine Expiry, Authenticity and Smart Reminders",
)

# Top Bar / Controls
col_title, col_ctrl = st.columns([3, 1])
with col_title:
    st.caption("Live monitoring of stored medicine inventory, expiration timelines, and daily scheduled doses.")
with col_ctrl:
    threshold_days = st.slider("Expiring Soon Window (Days)", min_value=7, max_value=90, value=DEFAULT_EXPIRING_SOON_DAYS, step=1)

# Fetch latest metrics
metrics = get_dashboard_summary_metrics(threshold_days=threshold_days)
medicines = get_all_medicines(threshold_days=threshold_days)
alerts = get_active_alerts(threshold_days=threshold_days)

# 1. SUMMARY CARDS (7 Core KPI Cards)
st.markdown("### 📊 Inventory & Adherence Overview")
row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)
with row1_col1:
    st.markdown(render_metric_card("Total Medicines", metrics["total_medicines"], "Registered in inventory", "#0F766E", "📦"), unsafe_allow_html=True)
with row1_col2:
    st.markdown(render_metric_card("Valid Medicines", metrics["valid_medicines"], "Safe stored expiry date", "#10B981", "✅"), unsafe_allow_html=True)
with row1_col3:
    st.markdown(render_metric_card("Expiring Soon", metrics["expiring_soon_medicines"], f"Within {threshold_days} days", "#F59E0B", "⏳"), unsafe_allow_html=True)
with row1_col4:
    st.markdown(render_metric_card("Expired Medicines", metrics["expired_medicines"], "Action required: do not use", "#EF4444", "⛔"), unsafe_allow_html=True)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

row2_col1, row2_col2, row2_col3 = st.columns(3)
with row2_col1:
    st.markdown(render_metric_card("Today's Reminders", metrics["today_reminders"], "Doses scheduled today", "#3B82F6", "⏰"), unsafe_allow_html=True)
with row2_col2:
    st.markdown(render_metric_card("Taken Doses (Today)", metrics["today_taken"], f"Total recorded: {metrics['all_time_taken']}", "#10B981", "✔️"), unsafe_allow_html=True)
with row2_col3:
    st.markdown(render_metric_card("Skipped Doses (Today)", metrics["today_skipped"], f"Total recorded: {metrics['all_time_skipped']}", "#64748B", "⏭️"), unsafe_allow_html=True)

st.divider()

# 2. PRIORITY SAFETY ALERTS SECTION
st.markdown("### 🚨 Priority Safety Alerts")
alert_tabs = st.tabs([
    f"⛔ Expired ({len(alerts['critical'])})",
    f"⏳ Expiring Soon ({len(alerts['warnings'])})",
    f"🕒 Pending Doses ({len(alerts['reminders'])})",
])

with alert_tabs[0]:
    if alerts["critical"]:
        for alt in alerts["critical"]:
            st.markdown(
                f"""
                <div class="safety-alert-critical">
                    <strong>⛔ {alt['title']}</strong> (Batch: <code>{alt['batch']}</code>)<br>
                    <span style="font-size: 0.88rem; color: #991b1b;">{alt['message']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        render_empty_state("No Expired Medicines Detected", "All stored medications currently satisfy valid shelf-life criteria.", icon="✅")

with alert_tabs[1]:
    if alerts["warnings"]:
        for alt in alerts["warnings"]:
            st.markdown(
                f"""
                <div class="safety-alert-warning">
                    <strong>⏳ {alt['title']}</strong> (Batch: <code>{alt['batch']}</code>)<br>
                    <span style="font-size: 0.88rem; color: #92400e;">{alt['message']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        render_empty_state("No Imminent Expirations", f"No registered pharmaceuticals will expire within the configured {threshold_days}-day window.", icon="🛡️")

with alert_tabs[2]:
    if alerts["reminders"]:
        for alt in alerts["reminders"]:
            st.warning(f"🕒 **{alt['title']}** — {alt['message']}")
    else:
        st.success("✅ All scheduled doses for today have been confirmed or recorded.")

st.divider()

# 3. TODAY'S MEDICATION REMINDER SCHEDULE & QUICK ACTION
st.markdown("### ⏰ Today's Medication Schedule")
today_doses = get_today_doses()

if today_doses:
    for dose in today_doses:
        with st.container():
            d_col1, d_col2, d_col3, d_col4 = st.columns([3, 2, 2, 3])
            with d_col1:
                st.markdown(f"**💊 {dose['medicine_name']}**")
                st.caption(f"Dosage: {dose['dosage']} | Mfr: {dose['manufacturer']}")
            with d_col2:
                time_only = dose['scheduled_time'].split(' ')[1][:5]
                st.markdown(f"**Scheduled:** `{time_only}`")
                if dose['actual_time']:
                    act_time = dose['actual_time'].split(' ')[1][:5]
                    st.caption(f"Logged at: {act_time}")
            with d_col3:
                badge_html = get_status_badge_html(dose['status'])
                st.markdown(badge_html, unsafe_allow_html=True)
            with d_col4:
                if dose['status'] == "PENDING":
                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        if st.button("Mark Taken", key=f"dash_taken_{dose['history_id']}", use_container_width=True):
                            mark_dose_status(dose['history_id'], DOSE_TAKEN, "Confirmed from Dashboard")
                            st.rerun()
                    with btn_c2:
                        if st.button("Mark Skipped", key=f"dash_skip_{dose['history_id']}", use_container_width=True):
                            mark_dose_status(dose['history_id'], DOSE_SKIPPED, "Skipped from Dashboard")
                            st.rerun()
                else:
                    st.caption(f"Logged as {dose['status']}")
            st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px solid #f1f5f9;'>", unsafe_allow_html=True)
else:
    render_empty_state("No Medication Doses Scheduled for Today", "Active routines can be configured in the Reminders module.", icon="⏰")

st.divider()

# 4. ANALYTICS & VISUALIZATIONS (PLOTLY)
st.markdown("### 📈 Visual Analytics & Reports")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    fig_status = create_status_distribution_chart(medicines)
    st.plotly_chart(fig_status, use_container_width=True)

with chart_col2:
    fig_adherence = create_dose_history_chart()
    st.plotly_chart(fig_adherence, use_container_width=True)

chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    fig_mfg = create_manufacturer_chart(medicines)
    st.plotly_chart(fig_mfg, use_container_width=True)

with chart_col4:
    fig_exp = create_upcoming_expiry_timeline(medicines)
    st.plotly_chart(fig_exp, use_container_width=True)

# Viva Explanation Note
with st.expander("🎓 Examiner Viva Information: Architecture & Logic"):
    render_viva_note(
        "Expiry Horizon & Adherence Calculation",
        "• <b>Real-time Delta Calculation</b>: Days remaining are evaluated on-the-fly via <code>(expiry_date - current_date)</code> rather than static cached status fields.<br>"
        "• <b>Adherence Compliance Engine</b>: Computes adherence rate as <code>(Taken Doses / [Taken + Skipped Doses]) * 100</code>, ensuring clinically meaningful compliance tracking.<br>"
        "• <b>Parameterized SQL Layer</b>: All database reads/writes use SQLite parameterized tuples, completely shielding against SQL injection.",
    )

# Academic disclaimer footer
render_academic_disclaimer()
