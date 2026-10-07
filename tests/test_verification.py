"""
Unit tests for MediSafe Verification Module.
Tests batch, barcode, and QR code verification, not-found behavior,
empty input handling, and audit logging.
"""

import pytest
from database import init_database, fetch_one
from verification import verify_identifier, get_verification_history
from config import (
    VERIFIED_FOUND,
    NOT_FOUND,
    VERIFICATION_REQUIRED,
    IDENTIFIER_BATCH,
    IDENTIFIER_BARCODE,
    IDENTIFIER_QR,
)


@pytest.fixture(autouse=True)
def setup_db():
    init_database()


def test_verification_batch_found():
    """Test verifying a valid seeded batch number returns VERIFIED RECORD FOUND."""
    # SUN-PARA-9821 is one of the standard seeded batches
    result = verify_identifier(IDENTIFIER_BATCH, "SUN-PARA-9821")

    assert result["status"] == VERIFIED_FOUND
    assert result["medicine"] is not None
    assert result["medicine"]["batch_number"] == "SUN-PARA-9821"
    assert "Paracetamol" in result["medicine"]["medicine_name"]


def test_verification_barcode_found():
    """Test verifying a valid barcode returns VERIFIED RECORD FOUND."""
    result = verify_identifier(IDENTIFIER_BARCODE, "8901030101112")

    assert result["status"] == VERIFIED_FOUND
    assert result["medicine"] is not None
    assert result["medicine"]["barcode"] == "8901030101112"


def test_verification_qr_string_found():
    """Test verifying an encoded QR string returns VERIFIED RECORD FOUND."""
    qr_str = "MEDISAFE|BATCH:SUN-PARA-9821|BARCODE:8901030101112"
    result = verify_identifier(IDENTIFIER_QR, qr_str)

    assert result["status"] == VERIFIED_FOUND
    assert result["medicine"] is not None
    assert result["medicine"]["batch_number"] == "SUN-PARA-9821"


def test_verification_not_found():
    """Test that a non-existent batch returns RECORD NOT FOUND."""
    result = verify_identifier(IDENTIFIER_BATCH, "FAKE-NONEXISTENT-BATCH-9999")

    assert result["status"] == NOT_FOUND
    assert result["medicine"] is None
    assert "No matching medicine record exists" in result["message"]


def test_verification_empty_requires_input():
    """Test that empty input returns VERIFICATION REQUIRED."""
    result = verify_identifier(IDENTIFIER_BATCH, "")

    assert result["status"] == VERIFICATION_REQUIRED
    assert result["medicine"] is None


def test_verification_audit_logged():
    """Test that verification actions are inserted into the audit log."""
    verify_identifier(IDENTIFIER_BATCH, "SUN-PARA-9821")
    history = get_verification_history(limit=5)

    assert len(history) > 0
    latest = history[0]
    assert latest["identifier_type"] == IDENTIFIER_BATCH
    assert latest["identifier_value"] == "SUN-PARA-9821"
    assert latest["verification_status"] == VERIFIED_FOUND
