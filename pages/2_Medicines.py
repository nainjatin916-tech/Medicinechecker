"""
MediSafe - 2. Medicines Catalog & Management
Browse, search, filter, inspect details, generate QR tags, edit, delete,
and export medicine inventory records.
"""

import streamlit as st
import pandas as pd
from config import APP_NAME, DEFAULT_EXPIRING_SOON_DAYS, UNITS
from database import init_database
from medicine import (
    get_all_medicines,
    get_all_manufacturers,
    delete_medicine,
    update_medicine,
    export_medicines_dataframe,
)
from verification import get_qr_image_bytes
from utils import (
    render_header,
    render_academic_disclaimer,
    get_status_badge_html,
    render_empty_state,
    render_viva_note,
)

st.set_page_config(
    page_title=f"{APP_NAME} - Medicines Inventory",
    page_icon="💊",
    layout="wide",
)

init_database()
render_header("Medicines Inventory", "Browse, search, edit, inspect, and export stored medicines")

# Search and Filters
col_search, col_status, col_mfg, col_sort = st.columns([3, 2, 2, 2])

with col_search:
    search_query = st.text_input("🔍 Search Inventory", placeholder="Name, Batch, Barcode, Manufacturer...")

with col_status:
    status_filter = st.selectbox(
        "Expiry Filter",
        options=["ALL", "VALID", "EXPIRING SOON", "EXPIRED"],
        index=0,
    )

with col_mfg:
    manufacturers = ["ALL"] + get_all_manufacturers()
    mfg_filter = st.selectbox("Manufacturer Filter", options=manufacturers, index=0)

with col_sort:
    sort_option = st.selectbox(
        "Sort By",
        options=[
            ("expiry_date_asc", "Expiry Date (Earliest)"),
            ("expiry_date_desc", "Expiry Date (Latest)"),
            ("days_remaining_asc", "Days Remaining (Urgent First)"),
            ("name_asc", "Name (A-Z)"),
            ("quantity_desc", "Quantity (High to Low)"),
        ],
        format_func=lambda x: x[1],
        index=0,
    )[0]

# Query medicines
medicines = get_all_medicines(
    search_query=search_query,
    status_filter=status_filter,
    manufacturer_filter=mfg_filter,
    sort_by=sort_option,
)

# Top action bar with count and CSV Export
col_count, col_export = st.columns([3, 1])
with col_count:
    st.write(f"Showing **{len(medicines)}** medicine record(s)")
with col_export:
    export_df = export_medicines_dataframe()
    if not export_df.empty:
        csv_data = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Inventory (CSV)",
            data=csv_data,
            file_name="medisafe_medicines_inventory.csv",
            mime="text/csv",
            use_container_width=True,
        )

st.markdown("<hr style='margin: 12px 0;'>", unsafe_allow_html=True)

if not medicines:
    render_empty_state(
        "No Matching Medicines Found",
        "No pharmaceutical records match the active search query or filter settings. Clear filters or add a new medicine.",
        icon="💊",
    )
else:
    for med in medicines:
        with st.expander(f"💊 **{med['medicine_name']}** — Batch: `{med['batch_number']}` | {med['manufacturer']}", expanded=False):
            detail_c1, detail_c2, detail_c3 = st.columns([3, 3, 2])

            with detail_c1:
                st.markdown(f"**Generic Name:** {med['generic_name'] or 'N/A'}")
                st.markdown(f"**Manufacturer:** {med['manufacturer']}")
                st.markdown(f"**Batch Number:** `{med['batch_number']}`")
                st.markdown(f"**Barcode:** `{med['barcode'] or 'N/A'}`")
                st.markdown(f"**Dosage:** {med['dosage']}")
                st.markdown(f"**Stock Quantity:** {med['quantity']} {med['unit']}")

            with detail_c2:
                st.markdown(f"**Manufacturing Date:** {med['manufacturing_date']}")
                st.markdown(f"**Expiry Date:** {med['expiry_date']}")
                badge = get_status_badge_html(med['expiry_status'], med['expiry_message'])
                st.markdown(f"**Expiry Classification:**<br>{badge}", unsafe_allow_html=True)
                st.markdown(f"**Notes:** {med['notes'] or 'None recorded'}")

            with detail_c3:
                st.markdown("**QR Identifier Tag:**")
                qr_payload = med['qr_code'] or f"MEDISAFE|BATCH:{med['batch_number']}|NAME:{med['medicine_name']}"
                qr_bytes = get_qr_image_bytes(qr_payload)
                if qr_bytes:
                    st.image(qr_bytes, width=130)
                    st.download_button(
                        label="Download QR",
                        data=qr_bytes,
                        file_name=f"qr_{med['batch_number']}.png",
                        mime="image/png",
                        key=f"dl_qr_{med['id']}",
                    )

            st.markdown("---")
            # Edit / Delete Section
            action_c1, action_c2 = st.columns([1, 1])

            with action_c1:
                # Edit Form inside an inner expander
                with st.popover("✏️ Edit Medicine Details"):
                    st.markdown(f"#### Edit {med['medicine_name']}")
                    with st.form(key=f"edit_form_{med['id']}"):
                        e_name = st.text_input("Medicine Name", value=med["medicine_name"])
                        e_gen = st.text_input("Generic Name", value=med["generic_name"] or "")
                        e_mfg = st.text_input("Manufacturer", value=med["manufacturer"])
                        e_batch = st.text_input("Batch Number", value=med["batch_number"])
                        e_barcode = st.text_input("Barcode", value=med["barcode"] or "")
                        e_dosage = st.text_input("Dosage", value=med["dosage"])
                        e_qty = st.number_input("Quantity", min_value=0.1, value=float(med["quantity"]), step=1.0)
                        
                        unit_idx = UNITS.index(med["unit"]) if med["unit"] in UNITS else 0
                        e_unit = st.selectbox("Unit", options=UNITS, index=unit_idx)

                        e_mfg_date = st.date_input("Manufacturing Date", value=pd.to_datetime(med["manufacturing_date"]).date())
                        e_exp_date = st.date_input("Expiry Date", value=pd.to_datetime(med["expiry_date"]).date())
                        e_notes = st.text_area("Notes", value=med["notes"] or "")

                        submitted = st.form_submit_button("Save Changes", use_container_width=True)
                        if submitted:
                            payload = {
                                "medicine_name": e_name,
                                "generic_name": e_gen,
                                "manufacturer": e_mfg,
                                "batch_number": e_batch,
                                "barcode": e_barcode,
                                "dosage": e_dosage,
                                "quantity": e_qty,
                                "unit": e_unit,
                                "manufacturing_date": str(e_mfg_date),
                                "expiry_date": str(e_exp_date),
                                "notes": e_notes,
                            }
                            success, msg = update_medicine(med["id"], payload)
                            if success:
                                st.success("Medicine updated!")
                                st.rerun()
                            else:
                                st.error(msg)

            with action_c2:
                with st.popover("🗑️ Delete Medicine"):
                    st.warning(f"Are you sure you want to delete '{med['medicine_name']}'?")
                    st.caption("This will also remove any associated reminders and scheduled dose history.")
                    if st.button("Confirm Delete", key=f"del_confirm_{med['id']}", type="primary"):
                        success, msg = delete_medicine(med["id"])
                        if success:
                            st.success("Deleted!")
                            st.rerun()
                        else:
                            st.error(msg)

with st.expander("🎓 Examiner Viva Information: Relational Schema & Cascades"):
    render_viva_note(
        "Inventory Schema Integrity",
        "• <b>Unique Constraint on Batch Numbers</b>: Enforces that each registered medicine has a unique lot number via SQLite <code>UNIQUE(batch_number)</code>.<br>"
        "• <b>Foreign Key ON DELETE CASCADE</b>: Deleting a medicine automatically cascades to delete all linked active reminders and historical dose logs, ensuring database referential integrity without orphan records.<br>"
        "• <b>Non-Destructive Audit Log</b>: Verification audit logs retain past checks with <code>ON DELETE SET NULL</code>, preserving security history even if inventory items are retired.",
    )

render_academic_disclaimer()
