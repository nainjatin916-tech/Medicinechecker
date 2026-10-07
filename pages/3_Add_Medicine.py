"""
MediSafe - 3. Add Medicine
Register a new medicine into the prototype database with validation,
dynamic expiry preview, and instant QR code generation.
"""

from datetime import date, timedelta
import streamlit as st
from config import APP_NAME, UNITS
from database import init_database
from medicine import add_medicine
from expiry_checker import get_expiry_status, validate_manufacturing_and_expiry
from verification import get_qr_image_bytes
from utils import render_header, render_academic_disclaimer, get_status_badge_html, render_viva_note

st.set_page_config(
    page_title=f"{APP_NAME} - Add Medicine",
    page_icon="➕",
    layout="wide",
)

init_database()
render_header("Register New Medicine", "Enter medicine specifications with validation and instant identifier tagging")

col_form, col_preview = st.columns([3, 2])

today = date.today()

with col_form:
    st.markdown("### 📝 Medicine Information")
    with st.form("add_medicine_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            med_name = st.text_input("Medicine Name *", placeholder="e.g., Paracetamol 650mg")
        with c2:
            gen_name = st.text_input("Generic Name (Optional)", placeholder="e.g., Acetaminophen")

        c3, c4 = st.columns(2)
        with c3:
            manufacturer = st.text_input("Manufacturer *", placeholder="e.g., Cipla Ltd")
        with c4:
            batch_num = st.text_input("Batch Number *", placeholder="e.g., CIP-PARA-2026A")

        c5, c6 = st.columns(2)
        with c5:
            barcode = st.text_input("Barcode Identifier (Optional)", placeholder="e.g., 8901030199991")
        with c6:
            dosage = st.text_input("Dosage Specification *", placeholder="e.g., 650 mg or 5 ml")

        c7, c8 = st.columns(2)
        with c7:
            quantity = st.number_input("Quantity in Stock *", min_value=1.0, value=10.0, step=1.0)
        with c8:
            unit = st.selectbox("Unit *", options=UNITS, index=0)

        c9, c10 = st.columns(2)
        with c9:
            mfg_date = st.date_input("Manufacturing Date *", value=today - timedelta(days=60))
        with c10:
            exp_date = st.date_input("Expiry Date *", value=today + timedelta(days=365))

        notes = st.text_area("Storage Notes / Medical Directions (Optional)", placeholder="e.g., Store below 25°C in a dry place.")

        submitted = st.form_submit_button("➕ Register Medicine", use_container_width=True, type="primary")

        if submitted:
            payload = {
                "medicine_name": med_name,
                "generic_name": gen_name,
                "manufacturer": manufacturer,
                "batch_number": batch_num,
                "barcode": barcode,
                "dosage": dosage,
                "quantity": quantity,
                "unit": unit,
                "manufacturing_date": str(mfg_date),
                "expiry_date": str(exp_date),
                "notes": notes,
            }
            success, message, new_id = add_medicine(payload)
            if success:
                st.success(f"✅ Medicine '{med_name}' successfully added (ID: {new_id})!")
                st.info("You can view or manage it in the 'Medicines' inventory tab.")
            else:
                st.error(f"❌ Registration Failed: {message}")

with col_preview:
    st.markdown("### 🔍 Live Preview & QR Tag")
    
    # Live Expiry Status calculation
    is_valid_dates, date_err = validate_manufacturing_and_expiry(mfg_date, exp_date)
    if not is_valid_dates:
        st.error(f"⚠️ {date_err}")
    else:
        status, days, msg = get_expiry_status(exp_date)
        st.markdown(f"**Predicted Expiry Status:**")
        badge = get_status_badge_html(status, msg)
        st.markdown(badge, unsafe_allow_html=True)
        st.caption(f"Calculated relative to today ({today.strftime('%Y-%m-%d')}).")

    st.markdown("<hr style='margin: 16px 0;'>", unsafe_allow_html=True)

    # Live QR Code Preview
    preview_batch = batch_num.strip() or "SAMPLE-BATCH-0000"
    preview_barcode = barcode.strip() or "000000000000"
    preview_name = med_name.strip() or "Sample Medicine"
    preview_payload = f"MEDISAFE|BATCH:{preview_batch}|BARCODE:{preview_barcode}|NAME:{preview_name}"

    st.markdown("**Live Generated QR Identifier:**")
    qr_bytes = get_qr_image_bytes(preview_payload)
    if qr_bytes:
        st.image(qr_bytes, width=180, caption=f"Tag for {preview_batch}")
        st.caption(f"Encoded payload: `{preview_payload}`")

with st.expander("🎓 Examiner Viva Information: Input Validation Rules"):
    render_viva_note(
        "Strict Pre-Persistence Validation",
        "• <b>Chronological Boundary Invariant</b>: <code>manufacturing_date &le; expiry_date</code> prevents logically invalid shelf-life entries.<br>"
        "• <b>Positive Inventory Invariant</b>: <code>quantity &gt; 0</code> prevents non-positive or negative stock registrations.<br>"
        "• <b>Relational Identity</b>: <code>batch_number</code> is enforced unique before executing the SQL <code>INSERT</code>.",
    )

render_academic_disclaimer()
