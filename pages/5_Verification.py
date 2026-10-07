"""
MediSafe - 5. Authenticity & Identifier Verification
Verifies Batch Number, Barcode, or QR identifiers against the trusted prototype database,
generates downloadable QR codes, and records an audit log.
"""

import streamlit as st
import pandas as pd
from config import (
    APP_NAME,
    IDENTIFIER_BATCH,
    IDENTIFIER_BARCODE,
    IDENTIFIER_QR,
    IDENTIFIER_TYPES,
    VERIFIED_FOUND,
    NOT_FOUND,
    VERIFICATION_REQUIRED,
    VERIFICATION_DISCLAIMER,
)
from database import init_database
from verification import verify_identifier, get_verification_history, get_qr_image_bytes
from medicine import get_all_medicines
from utils import (
    render_header,
    render_academic_disclaimer,
    get_status_badge_html,
    render_empty_state,
    render_viva_note,
)

st.set_page_config(
    page_title=f"{APP_NAME} - Verification",
    page_icon="🛡️",
    layout="wide",
)

init_database()
render_header("Identifier Verification", "Verify Batch Numbers, Barcodes, and QR tags against the trusted prototype registry")

st.info(f"🛡️ **System Scope**: {VERIFICATION_DISCLAIMER}")

verify_tab1, verify_tab2, verify_tab3 = st.tabs([
    "🔍 Verify Identifier",
    "📲 QR Code Generator",
    "📜 Verification Audit Log",
])

# 1. VERIFY IDENTIFIER TAB
with verify_tab1:
    st.markdown("### Search & Verify Identifier")
    st.caption("Enter a medicine batch code, barcode, or QR string to check if it exists in the prototype database.")

    # Quick demo selector helper
    all_meds = get_all_medicines()
    with st.expander("💡 Examiner Viva Quick-Test Presets (1-Click Test Scenarios)"):
        st.caption("Click any preset below to automatically fill and test the verification engine:")
        p_c1, p_c2, p_c3 = st.columns(3)
        with p_c1:
            if st.button("✅ Test Valid Batch (Metformin)", use_container_width=True):
                st.session_state["verify_input_val"] = "SUN-MET-8841"
                st.session_state["verify_type_val"] = IDENTIFIER_BATCH
                st.rerun()
        with p_c2:
            if st.button("⛔ Test Expired Batch (Paracetamol)", use_container_width=True):
                st.session_state["verify_input_val"] = "SUN-PARA-9821"
                st.session_state["verify_type_val"] = IDENTIFIER_BATCH
                st.rerun()
        with p_c3:
            if st.button("❌ Test Fake / Unregistered Batch", use_container_width=True):
                st.session_state["verify_input_val"] = "FAKE-LOT-9999"
                st.session_state["verify_type_val"] = IDENTIFIER_BATCH
                st.rerun()

    col_type, col_input = st.columns([1, 2])
    with col_type:
        default_type_idx = 0
        if "verify_type_val" in st.session_state and st.session_state["verify_type_val"] in IDENTIFIER_TYPES:
            default_type_idx = IDENTIFIER_TYPES.index(st.session_state["verify_type_val"])
        id_type = st.selectbox("Identifier Type", options=IDENTIFIER_TYPES, index=default_type_idx)

    with col_input:
        default_val = st.session_state.get("verify_input_val", "")
        id_val = st.text_input("Enter Identifier Value", value=default_val, placeholder="e.g. SUN-PARA-9821 or 8901030101112")

    if st.button("🔎 Verify Against Registry", type="primary", use_container_width=True):
        result = verify_identifier(id_type, id_val)
        st.markdown("<hr style='margin: 16px 0;'>", unsafe_allow_html=True)

        res_status = result["status"]
        if res_status == VERIFIED_FOUND:
            st.success(f"### ✅ {VERIFIED_FOUND}")
            st.markdown(get_status_badge_html(res_status), unsafe_allow_html=True)
            st.write(result["message"])

            med = result["medicine"]
            if med:
                res_c1, res_c2 = st.columns(2)
                with res_c1:
                    st.markdown(f"**Medicine Name:** {med['medicine_name']}")
                    st.markdown(f"**Manufacturer:** {med['manufacturer']}")
                    st.markdown(f"**Batch Number:** `{med['batch_number']}`")
                    st.markdown(f"**Dosage:** {med['dosage']}")
                with res_c2:
                    st.markdown(f"**Manufacturing Date:** {med['manufacturing_date']}")
                    st.markdown(f"**Expiry Date:** {med['expiry_date']}")
                    st.markdown(f"**Expiry Status:** {get_status_badge_html(med['expiry_status'], med['expiry_message'])}", unsafe_allow_html=True)
                    st.markdown(f"**Stock Quantity:** {med['quantity']} {med['unit']}")

            # Safety Warning
            st.warning(f"⚠️ **Notice**: {result['disclaimer']}")

        elif res_status == NOT_FOUND:
            st.error(f"### ❌ {NOT_FOUND}")
            st.markdown(get_status_badge_html(res_status), unsafe_allow_html=True)
            st.write(result["message"])
            st.warning("⚠️ This identifier does NOT match any authorized lot in the prototype database.")
            st.caption(f"Safety Rule: {result['disclaimer']}")

        else:
            st.warning(f"### ⚠️ {VERIFICATION_REQUIRED}")
            st.write(result["message"])

# 2. QR CODE GENERATOR TAB
with verify_tab2:
    st.markdown("### Generate Medicine QR Code")
    st.caption("Generate a high-resolution QR verification tag for any registered medicine or custom batch string.")

    if all_meds:
        selected_for_qr = st.selectbox(
            "Select registered medicine to generate QR:",
            options=all_meds,
            format_func=lambda m: f"{m['medicine_name']} — Batch: {m['batch_number']}",
            key="qr_gen_select",
        )
        custom_qr_content = st.text_input(
            "Payload String to Encode:",
            value=f"MEDISAFE|BATCH:{selected_for_qr['batch_number']}|BARCODE:{selected_for_qr['barcode'] or ''}|NAME:{selected_for_qr['medicine_name']}",
        )

        qr_img_bytes = get_qr_image_bytes(custom_qr_content)
        if qr_img_bytes:
            qr_col1, qr_col2 = st.columns([1, 2])
            with qr_col1:
                st.image(qr_img_bytes, width=220, caption=f"Tag: {selected_for_qr['batch_number']}")
            with qr_col2:
                st.markdown(f"**Medicine:** {selected_for_qr['medicine_name']}")
                st.markdown(f"**Batch:** `{selected_for_qr['batch_number']}`")
                st.markdown(f"**Manufacturer:** {selected_for_qr['manufacturer']}")
                st.markdown(f"**Encoded Data:** `{custom_qr_content}`")
                st.download_button(
                    label="💾 Download QR Code (PNG)",
                    data=qr_img_bytes,
                    file_name=f"medisafe_qr_{selected_for_qr['batch_number']}.png",
                    mime="image/png",
                    use_container_width=True,
                )
    else:
        st.warning("No medicines available to generate QR tags.")

# 3. VERIFICATION AUDIT LOG TAB
with verify_tab3:
    st.markdown("### Verification Audit History")
    st.caption("Records of all previous verification queries executed in this environment.")
    history = get_verification_history(limit=50)
    if history:
        df_hist = pd.DataFrame(history)
        st.dataframe(df_hist, use_container_width=True)
    else:
        render_empty_state("No Verification Checks Logged", "Verification lookups will automatically populate this audit registry.", icon="📜")

with st.expander("🎓 Examiner Viva Information: Verification Scope & Security Architecture"):
    render_viva_note(
        "Verification Matching vs Physical Authenticity",
        "• <b>Exact Identifier Query</b>: Matches user-supplied Batch, Barcode, or QR payloads against <code>medicines.batch_number</code> and <code>barcode</code> via SQL parameterized equality.<br>"
        "• <b>Tamper-Evident Audit Trail</b>: Every query attempt (both verified and unverified) is logged to <code>verification_records</code> with UTC timestamps for provenance tracking.<br>"
        "• <b>Medical Disclaimer Boundary</b>: A digital registry match proves record existence only; it cannot guarantee physical chemical integrity or cold-chain compliance.",
    )

render_academic_disclaimer()
