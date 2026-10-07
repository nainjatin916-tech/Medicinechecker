"""
MediSafe - Complete End-to-End QA Flow Test
Verifies all 17 user steps:
1. Open Dashboard
2. View sample medicines
3. Add a new medicine
4. Confirm expiry status calculated correctly
5. Edit the medicine
6. Search for the medicine
7. Verify its batch number
8. Verify an unknown batch number
9. Create a reminder
10. View the upcoming reminder
11. Mark a dose as Taken
12. Mark another dose as Skipped
13. Open Medication History
14. Check dashboard statistics
15. Export medicine data
16. Restart application
17. Confirm database data remains available
"""

import sqlite3
from datetime import date, timedelta
import pytest
from config import DATABASE_PATH
from database import init_database
from medicine import (
    add_medicine,
    update_medicine,
    get_medicine_by_id,
    get_all_medicines,
    export_medicines_dataframe,
)
from verification import verify_identifier
from reminder import (
    create_reminder,
    get_all_reminders,
    get_today_doses,
    mark_dose_status,
    get_medication_history,
)
from dashboard import get_dashboard_summary_metrics


def test_complete_17_step_qa_flow():
    # Step 1: Open Dashboard
    init_database()
    metrics_init = get_dashboard_summary_metrics()
    assert metrics_init["total_medicines"] >= 10, "Initial medicines must be >= 10"

    # Step 2: View sample medicines
    meds = get_all_medicines()
    assert len(meds) >= 10, "Failed to load sample medicines"
    expired = [m for m in meds if m["expiry_status"] == "EXPIRED"]
    expiring = [m for m in meds if m["expiry_status"] == "EXPIRING SOON"]
    valid = [m for m in meds if m["expiry_status"] == "VALID"]
    assert len(expired) > 0, "Sample data must include EXPIRED medicines"
    assert len(expiring) > 0, "Sample data must include EXPIRING SOON medicines"
    assert len(valid) > 0, "Sample data must include VALID medicines"

    # Step 3: Add a new medicine
    import time
    today = date.today()
    batch_num = f"QA-CIPRO-{int(time.time() * 1000)}"
    new_med_payload = {
        "medicine_name": "QA Ciprofloxacin 500mg",
        "generic_name": "Ciprofloxacin",
        "manufacturer": "QA Pharma Labs",
        "batch_number": batch_num,
        "barcode": "8901030998877",
        "dosage": "500 mg",
        "quantity": 30.0,
        "unit": "Tablets",
        "manufacturing_date": (today - timedelta(days=60)).strftime("%Y-%m-%d"),
        "expiry_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
        "notes": "Quality Assurance Test Record",
    }
    success, msg, new_med_id = add_medicine(new_med_payload)
    assert success is True and new_med_id is not None, f"Add medicine failed: {msg}"

    # Step 4: Confirm expiry status calculated correctly
    added_med = get_medicine_by_id(new_med_id)
    assert added_med is not None, "Failed to retrieve added medicine"
    assert added_med["expiry_status"] == "VALID", f"Expected VALID, got {added_med['expiry_status']}"
    assert added_med["days_remaining"] == 180, f"Expected 180 days, got {added_med['days_remaining']}"
    assert "Expires in 180 days" in added_med["expiry_message"]

    # Step 5: Edit the medicine
    edit_payload = dict(new_med_payload)
    edit_payload["dosage"] = "750 mg"
    edit_payload["quantity"] = 45.0
    edit_payload["notes"] = "Updated QA notes"
    edit_success, edit_msg = update_medicine(new_med_id, edit_payload)
    assert edit_success is True, f"Update failed: {edit_msg}"
    updated_med = get_medicine_by_id(new_med_id)
    assert updated_med["dosage"] == "750 mg", "Dosage was not updated"
    assert updated_med["quantity"] == 45.0, "Quantity was not updated"

    # Step 6: Search for the medicine
    search_by_batch = get_all_medicines(search_query=batch_num)
    assert len(search_by_batch) == 1, "Failed to find medicine by batch search"
    assert search_by_batch[0]["id"] == new_med_id
    search_by_name = get_all_medicines(search_query="Ciprofloxacin")
    assert len(search_by_name) >= 1, "Failed to find medicine by name search"

    # Step 7: Verify its batch number
    v_result = verify_identifier("Batch Number", batch_num)
    assert v_result["status"] == "VERIFIED RECORD FOUND"
    assert v_result["medicine"] is not None and v_result["medicine"]["id"] == new_med_id

    # Step 8: Verify an unknown batch number
    v_unknown = verify_identifier("Batch Number", "UNKNOWN-BATCH-999999")
    assert v_unknown["status"] == "RECORD NOT FOUND"
    assert v_unknown["medicine"] is None

    # Step 9: Create a reminder
    r_success, r_msg, rem_id = create_reminder(
        medicine_id=new_med_id,
        dosage="750 mg",
        reminder_time="09:00",
        frequency="Daily",
        start_date=today.strftime("%Y-%m-%d"),
        end_date=(today + timedelta(days=30)).strftime("%Y-%m-%d"),
    )
    assert r_success is True and rem_id is not None, f"Create reminder failed: {r_msg}"

    # Step 10: View the upcoming reminder
    all_rems = get_all_reminders()
    assert any(r["id"] == rem_id for r in all_rems), "Reminder schedule not found"
    today_doses = get_today_doses()
    matching_dose = [d for d in today_doses if d["medicine_id"] == new_med_id]
    assert len(matching_dose) >= 1, "Today's dose was not generated"

    # Step 11: Mark a dose as Taken
    target_dose_id = matching_dose[0]["history_id"]
    t_success, t_msg = mark_dose_status(target_dose_id, "TAKEN", "QA Taken Confirmation")
    assert t_success is True, f"Mark taken failed: {t_msg}"
    today_doses_post = get_today_doses()
    checked_taken = [d for d in today_doses_post if d["history_id"] == target_dose_id][0]
    assert checked_taken["status"] == "TAKEN"
    assert checked_taken["actual_time"] is not None

    # Step 12: Mark another dose as Skipped
    pending_doses = [d for d in today_doses_post if d["status"] == "PENDING"]
    second_dose_id = pending_doses[0]["history_id"] if pending_doses else today_doses_post[0]["history_id"]
    s_success, s_msg = mark_dose_status(second_dose_id, "SKIPPED", "QA Skipped Confirmation")
    assert s_success is True, f"Mark skipped failed: {s_msg}"
    today_doses_final = get_today_doses()
    checked_skipped = [d for d in today_doses_final if d["history_id"] == second_dose_id][0]
    assert checked_skipped["status"] == "SKIPPED"

    # Step 13: Open Medication History
    full_history = get_medication_history(status_filter="ALL")
    assert len(full_history) >= 2, "Medication history records insufficient"
    has_taken = any(h["status"] == "TAKEN" for h in full_history)
    has_skipped = any(h["status"] == "SKIPPED" for h in full_history)
    assert has_taken and has_skipped, "History must contain both TAKEN and SKIPPED entries"

    # Step 14: Check dashboard statistics
    metrics_updated = get_dashboard_summary_metrics()
    assert metrics_updated["total_medicines"] == metrics_init["total_medicines"] + 1
    assert metrics_updated["today_taken"] >= 1
    assert metrics_updated["today_skipped"] >= 1

    # Step 15: Export medicine data
    df_export = export_medicines_dataframe()
    assert not df_export.empty, "Exported DataFrame must not be empty"
    assert batch_num in df_export["batch_number"].values, "New batch missing from export"
    csv_bytes = df_export.to_csv(index=False).encode("utf-8")
    assert len(csv_bytes) > 200, "CSV bytes stream incomplete"

    # Step 16: Restart application (validate persistence on disk)
    fresh_conn = sqlite3.connect(str(DATABASE_PATH))
    fresh_conn.row_factory = sqlite3.Row
    c = fresh_conn.cursor()
    c.execute("SELECT COUNT(*) as c FROM medicines;")
    persisted_count = c.fetchone()["c"]
    fresh_conn.close()
    assert persisted_count == metrics_updated["total_medicines"]

    # Step 17: Confirm database data remains available
    persisted_med = get_medicine_by_id(new_med_id)
    assert persisted_med is not None
    assert persisted_med["batch_number"] == batch_num
    assert persisted_med["dosage"] == "750 mg"
    assert persisted_med["quantity"] == 45.0
    persisted_rems = get_all_reminders()
    assert any(r["id"] == rem_id for r in persisted_rems)
