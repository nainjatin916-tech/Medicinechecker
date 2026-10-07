"""
MediSafe - Main Application Entrypoint
"Medicine Expiry, Authenticity and Smart Reminders"
B.Tech CSE Academic Prototype Demonstration System.
"""

import streamlit as st
import sqlite3
from pathlib import Path
from config import (
    APP_NAME,
    APP_SUBTITLE,
    APP_TAGLINE,
    APP_VERSION,
    ACADEMIC_DISCLAIMER,
    DATABASE_PATH,
    LOGO_PATH,
)
from database import init_database, reset_database, fetch_one
from utils import ensure_logo, apply_custom_css, render_academic_disclaimer, render_viva_note

# Configure page
st.set_page_config(
    page_title=f"{APP_NAME} - Home",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply CSS & ensure assets exist
ensure_logo()
apply_custom_css()
init_database()

# SIDEBAR
with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
    else:
        st.title(f"🛡️ {APP_NAME}")

    st.markdown(f"**{APP_SUBTITLE}**")
    st.caption(f"*\"{APP_TAGLINE}\"*")
    st.markdown(f"**Version:** `{APP_VERSION}`")

    st.divider()

    # System Status
    st.markdown("### 🖥️ System Status")
    try:
        med_count = fetch_one("SELECT COUNT(*) as c FROM medicines;")["c"]
        rem_count = fetch_one("SELECT COUNT(*) as c FROM reminders;")["c"]
        st.success(f"● Database: Connected (`SQLite {sqlite3.sqlite_version}`)")
        st.info(f"● Stored Medicines: **{med_count}**")
        st.info(f"● Active Reminders: **{rem_count}**")
    except Exception as e:
        st.error(f"● Database Error: {e}")

    st.divider()

    # Evaluator Demo Tools
    st.markdown("### 🛠️ Evaluator Tools")
    if st.button("🔄 Reset Demo Database", help="Reinitializes sample medicines, reminders, and doses"):
        reset_database()
        st.success("Database reset with fresh sample data!")
        st.rerun()

    st.divider()
    st.caption("Developed for B.Tech CSE Project Evaluation.")

# MAIN PAGE CONTENT
st.markdown(
    f"""
    <div class="medisafe-header-container">
        <div class="medisafe-header-title">
            🛡️ {APP_NAME}
        </div>
        <div class="medisafe-header-subtitle">{APP_SUBTITLE}</div>
        <div class="medisafe-header-tagline">"{APP_TAGLINE}"</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    Welcome to **MediSafe**, an integrated healthcare safety prototype engineered to eliminate
    the risks of accidental consumption of expired medications, verify packaging identifiers
    against a trusted prototype database, and provide timely reminders for daily dosage regimens.
    """
)

# Mandatory Academic Safety Alert
st.warning(
    f"⚠️ **IMPORTANT ACADEMIC PROTOTYPE NOTICE**:\n\n"
    f"{ACADEMIC_DISCLAIMER}"
)

st.markdown("### 🚀 System Modules & Navigation")
st.caption("Select a module from the left sidebar or use the quick access links below:")

c1, c2 = st.columns(2)

with c1:
    st.page_link("pages/1_Dashboard.py", label="1. Dashboard Overview", icon="📊")
    st.caption("• High-level KPIs (Total, Valid, Expiring Soon, Expired, Today's Reminders)\n• Priority Safety Alerts & immediate action prompts\n• Interactive Plotly visualizations for shelf-life & adherence")

    st.page_link("pages/2_Medicines.py", label="2. Medicines Inventory", icon="💊")
    st.caption("• Complete catalog of registered pharmaceuticals\n• Search by name, manufacturer, batch number, or barcode\n• Filter by expiration state & export inventory to CSV")

    st.page_link("pages/3_Add_Medicine.py", label="3. Register Medicine", icon="➕")
    st.caption("• Form validation with strict date rules (Mfg ≤ Exp)\n• Live expiration forecast relative to today\n• Automatic QR identifier generation")

with c2:
    st.page_link("pages/4_Expiry_Checker.py", label="4. Expiry Checker", icon="⏳")
    st.caption("• Configurable warning threshold (default: 30 days)\n• Days remaining countdown for all stored lots\n• Interactive simulation sandbox for test dates")

    st.page_link("pages/5_Verification.py", label="5. Identifier Verification", icon="🛡️")
    st.caption("• Multi-identifier verification (Batch, Barcode, QR)\n• Immediate match status vs prototype database\n• Downloadable QR code tag generation")

    st.page_link("pages/6_Reminders.py", label="6. Reminders & Dose Tracking", icon="⏰")
    st.caption("• Daily / Weekly / Once dosage schedules\n• One-click 'Mark Taken' and 'Mark Skipped' actions\n• Duplicate dose prevention for scheduled slots")

    st.page_link("pages/7_History.py", label="7. Medication History", icon="📜")
    st.caption("• Complete intake compliance audit trail\n• Adherence rate (%) computation & CSV export")

st.divider()

# Core Prototype Architecture
st.markdown("### 🏛️ System Architecture")
st.markdown(
    """
    ```text
    USER INTERFACE (Streamlit Multi-Page Web App)
          │
          ├── Dashboard & Safety Alerts (Plotly + In-App Notifications)
          ├── Medicine Management (CRUD, Search, Filter, CSV Export)
          ├── Expiry Analysis Engine (Configurable Days Remaining)
          ├── Verification Engine (Batch/Barcode/QR Lookup + Audit Log)
          └── Smart Reminder Engine (Scheduling, Doses, Duplicate Prevention)
          │
    APPLICATION LOGIC LAYER (Python 3.10)
          │
    DATABASE STORAGE LAYER (SQLite3 with Parameterized SQL & Foreign Keys)
          └── data/medsafe.db (medicines, reminders, verification_records, medication_history)
    ```
    """
)

with st.expander("🎓 Examiner Viva Information: Project Objectives & Defense Summary"):
    render_viva_note(
        "B.Tech CSE Capstone Defense Guide",
        "• <b>Objective 1: Expiry Mitigation</b>: Automates algorithmic shelf-life classification with customizable danger windows, reducing inadvertent toxicity.<br>"
        "• <b>Objective 2: Identifier Verification</b>: Matches Batch/Barcode/QR strings against a prototype repository, logging all queries into an audit log.<br>"
        "• <b>Objective 3: Dose Compliance Tracking</b>: Manages multi-frequency daily regimens with instant status toggling and duplicate prevention.<br>"
        "• <b>Zero-Config Portability</b>: Self-initializing embedded SQLite database with dynamic date offsetting ensures immediate examiner demonstration.",
    )

render_academic_disclaimer()
