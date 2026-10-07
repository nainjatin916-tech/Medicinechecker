"""
Unit tests for MediSafe Expiry Checker module.
Tests core classification logic, days remaining, threshold changes, and validation.
"""

from datetime import date, timedelta
import pytest
from expiry_checker import (
    get_expiry_status,
    validate_manufacturing_and_expiry,
    parse_date,
)
from config import STATUS_EXPIRED, STATUS_EXPIRING_SOON, STATUS_VALID


def test_expired_medicine():
    """Test that a past date is correctly classified as EXPIRED."""
    today = date.today()
    past_date = today - timedelta(days=15)
    status, days, msg = get_expiry_status(past_date)

    assert status == STATUS_EXPIRED
    assert days == -15
    assert "Expired 15 days ago" in msg


def test_expiring_soon_medicine():
    """Test that a date within the default 30-day window is EXPIRING SOON."""
    today = date.today()
    soon_date = today + timedelta(days=12)
    status, days, msg = get_expiry_status(soon_date, threshold_days=30)

    assert status == STATUS_EXPIRING_SOON
    assert days == 12
    assert "Expires in 12 days" in msg


def test_valid_medicine():
    """Test that a date well beyond the threshold is VALID."""
    today = date.today()
    future_date = today + timedelta(days=180)
    status, days, msg = get_expiry_status(future_date, threshold_days=30)

    assert status == STATUS_VALID
    assert days == 180
    assert "Expires in 180 days" in msg


def test_expires_today():
    """Test that an expiry date of today is treated as expiring soon/today."""
    today = date.today()
    status, days, msg = get_expiry_status(today)

    assert status == STATUS_EXPIRING_SOON
    assert days == 0
    assert "Expires today" in msg


def test_custom_threshold():
    """Test that changing threshold changes classification from VALID to EXPIRING SOON."""
    today = date.today()
    target_date = today + timedelta(days=40)

    # With default 30 days -> VALID
    status_30, _, _ = get_expiry_status(target_date, threshold_days=30)
    assert status_30 == STATUS_VALID

    # With expanded 60 days -> EXPIRING SOON
    status_60, _, _ = get_expiry_status(target_date, threshold_days=60)
    assert status_60 == STATUS_EXPIRING_SOON


def test_mfg_date_after_exp_date_invalid():
    """Test that manufacturing date after expiry date fails validation."""
    mfg = "2026-05-01"
    exp = "2026-01-01"
    is_valid, err = validate_manufacturing_and_expiry(mfg, exp)

    assert is_valid is False
    assert "cannot be later than" in err


def test_mfg_date_before_exp_date_valid():
    """Test that normal chronological manufacturing and expiry dates pass."""
    mfg = "2025-01-01"
    exp = "2027-01-01"
    is_valid, err = validate_manufacturing_and_expiry(mfg, exp)

    assert is_valid is True
    assert err == ""
