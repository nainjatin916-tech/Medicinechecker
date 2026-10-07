"""
MediSafe - Expiry Checker Module
Core business logic for calculating medicine expiry status, remaining days,
and formatted human-readable descriptions.
"""

from datetime import date, datetime
from typing import Tuple, Dict, Any, Union
from config import (
    DEFAULT_EXPIRING_SOON_DAYS,
    STATUS_EXPIRED,
    STATUS_EXPIRING_SOON,
    STATUS_VALID,
)


def parse_date(date_val: Union[str, date, datetime]) -> date:
    """
    Safely parses an input into a datetime.date object.
    Supports YYYY-MM-DD string, date, or datetime objects.
    """
    if isinstance(date_val, datetime):
        return date_val.date()
    if isinstance(date_val, date):
        return date_val
    if isinstance(date_val, str):
        # Handle string formats like YYYY-MM-DD or YYYY-MM-DD HH:MM:SS
        clean_str = date_val.strip().split(" ")[0]
        return datetime.strptime(clean_str, "%Y-%m-%d").date()
    raise ValueError(f"Unsupported date format or type: {type(date_val)} ({date_val})")


def get_expiry_status(
    expiry_date_val: Union[str, date, datetime],
    threshold_days: int = DEFAULT_EXPIRING_SOON_DAYS,
    reference_date: Union[str, date, datetime] = None,
) -> Tuple[str, int, str]:
    """
    Calculates the expiry status, days remaining, and human-readable message.

    Parameters:
        expiry_date_val: The expiry date as string 'YYYY-MM-DD' or date object.
        threshold_days: Number of days within which medicine is considered 'EXPIRING SOON'.
        reference_date: Optional reference date (defaults to today's date).

    Returns:
        tuple: (status, days_remaining, display_message)
            - status: 'EXPIRED' | 'EXPIRING SOON' | 'VALID'
            - days_remaining: integer (negative if expired, 0 if today, positive if future)
            - display_message: e.g., 'Expired 15 days ago', 'Expires today', 'Expires in 12 days'
    """
    exp_date = parse_date(expiry_date_val)
    ref_date = parse_date(reference_date) if reference_date else date.today()

    delta_days = (exp_date - ref_date).days

    if delta_days < 0:
        abs_days = abs(delta_days)
        day_str = "day" if abs_days == 1 else "days"
        status = STATUS_EXPIRED
        message = f"Expired {abs_days} {day_str} ago"
    elif delta_days == 0:
        status = STATUS_EXPIRING_SOON
        message = "Expires today!"
    elif delta_days <= threshold_days:
        day_str = "day" if delta_days == 1 else "days"
        status = STATUS_EXPIRING_SOON
        message = f"Expires in {delta_days} {day_str}"
    else:
        day_str = "day" if delta_days == 1 else "days"
        status = STATUS_VALID
        message = f"Expires in {delta_days} {day_str}"

    return status, delta_days, message


def evaluate_medicine_expiry(
    medicine_dict: Dict[str, Any],
    threshold_days: int = DEFAULT_EXPIRING_SOON_DAYS,
    reference_date: Union[str, date, datetime] = None,
) -> Dict[str, Any]:
    """
    Takes a medicine dictionary and injects expiry status metadata into a copy.
    """
    enriched = dict(medicine_dict)
    exp_date_raw = medicine_dict.get("expiry_date")
    status, days, msg = get_expiry_status(exp_date_raw, threshold_days, reference_date)
    enriched["expiry_status"] = status
    enriched["days_remaining"] = days
    enriched["expiry_message"] = msg
    return enriched


def validate_manufacturing_and_expiry(
    mfg_date_val: Union[str, date],
    exp_date_val: Union[str, date],
) -> Tuple[bool, str]:
    """
    Validates that manufacturing date is strictly before or equal to expiry date.
    Returns (is_valid, error_message).
    """
    try:
        mfg = parse_date(mfg_date_val)
        exp = parse_date(exp_date_val)
    except Exception as e:
        return False, f"Invalid date format: {str(e)}"

    if mfg > exp:
        return (
            False,
            f"Manufacturing date ({mfg}) cannot be later than Expiry date ({exp}).",
        )

    return True, ""
