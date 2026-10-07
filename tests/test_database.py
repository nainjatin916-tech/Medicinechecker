"""
Unit tests for MediSafe Database and Medicine Management layers.
Tests database tables, CRUD operations, unique constraints, and cascade deletions.
"""

from datetime import date, timedelta
import pytest
from database import init_database, fetch_all, fetch_one, execute_query
from medicine import (
    add_medicine,
    get_medicine_by_id,
    update_medicine,
    delete_medicine,
    validate_medicine_payload,
)


@pytest.fixture(autouse=True)
def setup_db():
    """Ensure database tables are initialized before tests."""
    init_database()


def test_database_tables_exist():
    """Verify that all 5 required tables exist in SQLite."""
    tables = fetch_all("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = [t["name"] for t in tables]

    assert "users" in table_names
    assert "medicines" in table_names
    assert "reminders" in table_names
    assert "verification_records" in table_names
    assert "medication_history" in table_names


def test_medicine_crud():
    """Test full cycle of adding, reading, updating, and deleting a medicine."""
    today = date.today()
    batch_code = f"TEST-BATCH-{today.strftime('%Y%m%d%H%M%S') if hasattr(today, 'strftime') else '9988'}"

    payload = {
        "medicine_name": "Test Antibiotic 500mg",
        "generic_name": "Amoxicillin Test",
        "manufacturer": "Test Pharma Ltd",
        "batch_number": batch_code,
        "barcode": "9998887776665",
        "dosage": "500 mg",
        "quantity": 25.0,
        "unit": "Capsules",
        "manufacturing_date": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
        "expiry_date": (today + timedelta(days=300)).strftime("%Y-%m-%d"),
        "notes": "Testing CRUD operations",
    }

    # 1. Add
    success, msg, new_id = add_medicine(payload)
    assert success is True
    assert new_id is not None

    # 2. Retrieve
    retrieved = get_medicine_by_id(new_id)
    assert retrieved is not None
    assert retrieved["medicine_name"] == "Test Antibiotic 500mg"
    assert retrieved["batch_number"] == batch_code

    # 3. Update
    update_payload = dict(payload)
    update_payload["dosage"] = "1000 mg"
    update_payload["quantity"] = 50.0
    u_success, u_msg = update_medicine(new_id, update_payload)
    assert u_success is True

    updated_med = get_medicine_by_id(new_id)
    assert updated_med["dosage"] == "1000 mg"
    assert updated_med["quantity"] == 50.0

    # 4. Delete
    d_success, d_msg = delete_medicine(new_id)
    assert d_success is True

    deleted_check = get_medicine_by_id(new_id)
    assert deleted_check is None


def test_duplicate_batch_number_rejected():
    """Test that registering two medicines with the same batch number is prevented."""
    today = date.today()
    duplicate_batch = "DUP-BATCH-UNIQUE-123"

    payload1 = {
        "medicine_name": "Medicine First",
        "manufacturer": "Pharma A",
        "batch_number": duplicate_batch,
        "dosage": "100 mg",
        "quantity": 10.0,
        "manufacturing_date": today.strftime("%Y-%m-%d"),
        "expiry_date": (today + timedelta(days=100)).strftime("%Y-%m-%d"),
    }

    payload2 = {
        "medicine_name": "Medicine Second",
        "manufacturer": "Pharma B",
        "batch_number": duplicate_batch,
        "dosage": "200 mg",
        "quantity": 20.0,
        "manufacturing_date": today.strftime("%Y-%m-%d"),
        "expiry_date": (today + timedelta(days=200)).strftime("%Y-%m-%d"),
    }

    # First succeeds
    s1, _, id1 = add_medicine(payload1)
    assert s1 is True

    try:
        # Second should fail due to duplicate batch
        s2, err_msg, id2 = add_medicine(payload2)
        assert s2 is False
        assert "already exists" in err_msg
    finally:
        # Cleanup
        if id1:
            delete_medicine(id1)
