"""
MediSafe - 4. Expiry Checker
Dedicated inspection tool for medicine expiration analysis, days remaining calculations,
threshold adjustments, and safety categorization.
"""

from datetime import date, timedelta
import streamlit as st
import pandas as pd
from config import (
    APP_NAME,
    DEFAULT_EXPIRING_SOON_DAYS,
    STATUS_EXPIRED,
    STATUS_EXPIRING_SOON,
    STATUS_VALID,
)
from database import init_database
from medicine import get_all_medicines
from expiry_checker import get_expiry_status
from utils import (
    render_header,
    render_academic_disclaimer,
    get_status_badge_html,
    render_metric_card,
    render_empty_state,
    render_viva_note,
)

st.set_page_config(
    page_title=f"{APP_NAME} - Expiry Checker",
    page_icon="⏳",
    layout="wide",
)

init_database()
render_header("Expiry Checker", "Classify expiration status, compute shelf-life countdowns, and set safety alert windows")

# Interactive Threshold and Simulator
col_sim, col_thresh = st.columns([1, 1])

with col_thresh:
    st.markdown("### ⚙️ Threshold Settings")
    threshold_days = st.slider(
        "Expiring Soon Alert Threshold (Days)",
        min_value=5,
        max_value=90,
        value=DEFAULT_EXPIRING_SOON_DAYS,
        step=5,
        help="Medicines expiring within this number of days will be flagged as 'EXPIRING SOON'.",
    )
    st.info(f"Rules Applied:\n- **EXPIRED**: Expiry date earlier than today ({date.today()})\n- **EXPIRING SOON**: Expiry date within {threshold_days} days\n- **VALID**: Expiry date more than {threshold_days} days in the future")

with col_sim:
    st.markdown("### 🧪 Date Checker Simulator")
    test_date = st.date_input("Select Any Expiry Date to Test", value=date.today() + timedelta(days=12))
    sim_status, sim_days, sim_msg = get_expiry_status(test_date, threshold_days=threshold_days)
    st.markdown("**Calculated Evaluation:**")
    st.markdown(get_status_badge_html(sim_status, sim_msg), unsafe_allow_html=True)
    st.caption(f"Difference: {sim_days} day(s) relative to {date.today()}.")

st.divider()

# Inventory Expiry Analysis
st.markdown("### 📋 Stored Inventory Expiry Analysis")
medicines = get_all_medicines(threshold_days=threshold_days)

expired_list = [m for m in medicines if m["expiry_status"] == STATUS_EXPIRED]
expiring_list = [m for m in medicines if m["expiry_status"] == STATUS_EXPIRING_SOON]
valid_list = [m for m in medicines if m["expiry_status"] == STATUS_VALID]

# Top KPI Summary
kpi_c1, kpi_c2, kpi_c3 = st.columns(3)
with kpi_c1:
    st.markdown(render_metric_card("Expired Items", len(expired_list), "Action: Safe disposal", "#EF4444", "⛔"), unsafe_allow_html=True)
with kpi_c2:
    st.markdown(render_metric_card("Expiring Soon", len(expiring_list), f"Within {threshold_days} days", "#F59E0B", "⏳"), unsafe_allow_html=True)
with kpi_c3:
    st.markdown(render_metric_card("Valid Items", len(valid_list), f"> {threshold_days} days shelf life", "#10B981", "✅"), unsafe_allow_html=True)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# Categorized Tabs
tab1, tab2, tab3 = st.tabs([
    f"⛔ Expired Medicines ({len(expired_list)})",
    f"⏳ Expiring Soon ({len(expiring_list)})",
    f"✅ Valid Medicines ({len(valid_list)})",
])

with tab1:
    if expired_list:
        st.error("⚠️ The following medicines have passed their stored expiration date. Do not consume.")
        exp_table = []
        for m in expired_list:
            exp_table.append({
                "Medicine": m["medicine_name"],
                "Batch Number": m["batch_number"],
                "Manufacturer": m["manufacturer"],
                "Expiry Date": m["expiry_date"],
                "Time Past Expiry": m["expiry_message"],
                "Days Passed": abs(m["days_remaining"]),
                "Stock": f"{m['quantity']} {m['unit']}",
            })
        st.dataframe(pd.DataFrame(exp_table), use_container_width=True)
    else:
        render_empty_state("No Expired Items", "All stored medicines currently satisfy valid shelf life criteria.", icon="✅")

with tab2:
    if expiring_list:
        st.warning(f"⏳ The following medicines will expire within {threshold_days} days.")
        soon_table = []
        for m in expiring_list:
            soon_table.append({
                "Medicine": m["medicine_name"],
                "Batch Number": m["batch_number"],
                "Manufacturer": m["manufacturer"],
                "Expiry Date": m["expiry_date"],
                "Countdown": m["expiry_message"],
                "Days Remaining": m["days_remaining"],
                "Stock": f"{m['quantity']} {m['unit']}",
            })
        st.dataframe(pd.DataFrame(soon_table), use_container_width=True)
    else:
        render_empty_state("No Imminent Expirations", f"No medicines are approaching expiration within the selected {threshold_days}-day horizon.", icon="🛡️")

with tab3:
    if valid_list:
        st.success("✅ The following medicines are within their valid shelf-life window.")
        val_table = []
        for m in valid_list:
            val_table.append({
                "Medicine": m["medicine_name"],
                "Batch Number": m["batch_number"],
                "Manufacturer": m["manufacturer"],
                "Expiry Date": m["expiry_date"],
                "Days Remaining": m["days_remaining"],
                "Stock": f"{m['quantity']} {m['unit']}",
            })
        st.dataframe(pd.DataFrame(val_table), use_container_width=True)
    else:
        render_empty_state("No Valid Inventory", "No active medicines found in the database.", icon="📦")

with st.expander("🎓 Examiner Viva Information: Expiry Horizon Boundary Conditions"):
    render_viva_note(
        "Boundary Classification Invariants",
        "• <b>Past Date (delta &lt; 0)</b>: Evaluates to <code>EXPIRED</code> unconditionally.<br>"
        "• <b>Same-Day Expiration (delta == 0)</b>: Treated as <code>EXPIRING SOON</code> ('Expires today!') to prioritize urgent patient safety.<br>"
        "• <b>Dynamic Reclassification</b>: Changing the threshold slider re-evaluates all records instantly without requiring database updates.",
    )

render_academic_disclaimer()
