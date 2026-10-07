"""
MediSafe - Medicine Management Module
Business logic and database operations for adding, editing, deleting,
searching, filtering, and exporting medicines.
"""

from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from database import execute_query, fetch_all, fetch_one
from expiry_checker import evaluate_medicine_expiry, validate_manufacturing_and_expiry
from config import DEFAULT_EXPIRING_SOON_DAYS


def validate_medicine_payload(payload: Dict[str, Any], is_update: bool = False, current_id: Optional[int] = None) -> Tuple[bool, List[str]]:
    """
    Validates medicine input data.
    Required fields:
        - Medicine Name
        - Manufacturer
        - Batch Number
        - Manufacturing Date
        - Expiry Date
        - Dosage
        - Quantity (> 0)
    Ensures manufacturing date is not after expiry date.
    Ensures batch number is unique.
    """
    errors: List[str] = []

    name = str(payload.get("medicine_name", "")).strip()
    mfg = str(payload.get("manufacturer", "")).strip()
    batch = str(payload.get("batch_number", "")).strip()
    mfg_date = payload.get("manufacturing_date")
    exp_date = payload.get("expiry_date")
    dosage = str(payload.get("dosage", "")).strip()
    quantity = payload.get("quantity")

    if not name:
        errors.append("Medicine Name is required.")
    if not mfg:
        errors.append("Manufacturer is required.")
    if not batch:
        errors.append("Batch Number is required.")
    if not dosage:
        errors.append("Dosage is required (e.g., '500 mg', '10 ml').")

    if quantity is None:
        errors.append("Quantity is required.")
    else:
        try:
            qty_float = float(quantity)
            if qty_float <= 0:
                errors.append("Quantity must be greater than 0.")
        except (ValueError, TypeError):
            errors.append("Quantity must be a valid numeric value.")

    if not mfg_date:
        errors.append("Manufacturing Date is required.")
    if not exp_date:
        errors.append("Expiry Date is required.")

    if mfg_date and exp_date:
        valid_dates, date_err = validate_manufacturing_and_expiry(mfg_date, exp_date)
        if not valid_dates:
            errors.append(date_err)

    # Check for duplicate batch number
    if batch:
        if is_update and current_id:
            existing = fetch_one(
                "SELECT id FROM medicines WHERE UPPER(batch_number) = UPPER(?) AND id != ?;",
                (batch, current_id),
            )
        else:
            existing = fetch_one(
                "SELECT id FROM medicines WHERE UPPER(batch_number) = UPPER(?);",
                (batch,),
            )
        if existing:
            errors.append(f"Batch Number '{batch}' already exists in the database. Batch numbers must be unique.")

    return len(errors) == 0, errors


def add_medicine(payload: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
    """
    Adds a new medicine after validation.
    Returns (success, message, new_medicine_id).
    """
    is_valid, errors = validate_medicine_payload(payload)
    if not is_valid:
        return False, " | ".join(errors), None

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Generate a standard QR code payload string if none provided
    batch = payload["batch_number"].strip()
    barcode = str(payload.get("barcode", "")).strip()
    name = payload["medicine_name"].strip()
    qr_code = payload.get("qr_code") or f"MEDISAFE|BATCH:{batch}|BARCODE:{barcode}|NAME:{name}"

    sql = """
        INSERT INTO medicines (
            user_id, medicine_name, generic_name, manufacturer, batch_number,
            barcode, qr_code, manufacturing_date, expiry_date, dosage,
            quantity, unit, notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    params = (
        payload.get("user_id", 1),
        name,
        str(payload.get("generic_name", "")).strip(),
        payload["manufacturer"].strip(),
        batch,
        barcode,
        qr_code,
        str(payload["manufacturing_date"]).split(" ")[0],
        str(payload["expiry_date"]).split(" ")[0],
        payload["dosage"].strip(),
        float(payload["quantity"]),
        str(payload.get("unit", "Tablets")).strip(),
        str(payload.get("notes", "")).strip(),
        now_str,
        now_str,
    )

    try:
        new_id = execute_query(sql, params)
        return True, "Medicine successfully added.", new_id
    except Exception as e:
        return False, f"Database error: {str(e)}", None


def update_medicine(medicine_id: int, payload: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Updates an existing medicine by ID after validation.
    Returns (success, message).
    """
    is_valid, errors = validate_medicine_payload(payload, is_update=True, current_id=medicine_id)
    if not is_valid:
        return False, " | ".join(errors)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch = payload["batch_number"].strip()
    barcode = str(payload.get("barcode", "")).strip()
    name = payload["medicine_name"].strip()
    qr_code = payload.get("qr_code") or f"MEDISAFE|BATCH:{batch}|BARCODE:{barcode}|NAME:{name}"

    sql = """
        UPDATE medicines SET
            medicine_name = ?,
            generic_name = ?,
            manufacturer = ?,
            batch_number = ?,
            barcode = ?,
            qr_code = ?,
            manufacturing_date = ?,
            expiry_date = ?,
            dosage = ?,
            quantity = ?,
            unit = ?,
            notes = ?,
            updated_at = ?
        WHERE id = ?;
    """
    params = (
        name,
        str(payload.get("generic_name", "")).strip(),
        payload["manufacturer"].strip(),
        batch,
        barcode,
        qr_code,
        str(payload["manufacturing_date"]).split(" ")[0],
        str(payload["expiry_date"]).split(" ")[0],
        payload["dosage"].strip(),
        float(payload["quantity"]),
        str(payload.get("unit", "Tablets")).strip(),
        str(payload.get("notes", "")).strip(),
        now_str,
        medicine_id,
    )

    try:
        execute_query(sql, params)
        return True, "Medicine updated successfully."
    except Exception as e:
        return False, f"Database error: {str(e)}"


def delete_medicine(medicine_id: int) -> Tuple[bool, str]:
    """
    Deletes a medicine and relies on cascade deletion for associated reminders and doses.
    """
    try:
        execute_query("DELETE FROM medicines WHERE id = ?;", (medicine_id,))
        return True, "Medicine deleted successfully."
    except Exception as e:
        return False, f"Database error: {str(e)}"


def get_medicine_by_id(medicine_id: int, threshold_days: int = DEFAULT_EXPIRING_SOON_DAYS) -> Optional[Dict[str, Any]]:
    """
    Retrieves a single medicine enriched with expiry classification.
    """
    med = fetch_one("SELECT * FROM medicines WHERE id = ?;", (medicine_id,))
    if not med:
        return None
    return evaluate_medicine_expiry(med, threshold_days)


def get_all_medicines(
    search_query: str = "",
    status_filter: str = "ALL",
    manufacturer_filter: str = "ALL",
    sort_by: str = "expiry_date_asc",
    threshold_days: int = DEFAULT_EXPIRING_SOON_DAYS,
) -> List[Dict[str, Any]]:
    """
    Fetches medicines with global search, filters, and sorting.
    Enriches each record with calculated expiry status and days remaining.
    """
    sql = "SELECT * FROM medicines WHERE 1=1"
    params: List[Any] = []

    if search_query:
        q = f"%{search_query.strip()}%"
        sql += """ AND (
            medicine_name LIKE ? OR
            generic_name LIKE ? OR
            batch_number LIKE ? OR
            barcode LIKE ? OR
            manufacturer LIKE ?
        )"""
        params.extend([q, q, q, q, q])

    if manufacturer_filter and manufacturer_filter != "ALL":
        sql += " AND manufacturer = ?"
        params.append(manufacturer_filter)

    rows = fetch_all(sql, tuple(params))
    enriched_rows = [evaluate_medicine_expiry(r, threshold_days) for r in rows]

    # Filter by expiry status if requested
    if status_filter and status_filter != "ALL":
        enriched_rows = [r for r in enriched_rows if r["expiry_status"] == status_filter]

    # Sorting
    if sort_by == "expiry_date_asc":
        enriched_rows.sort(key=lambda x: x["expiry_date"])
    elif sort_by == "expiry_date_desc":
        enriched_rows.sort(key=lambda x: x["expiry_date"], reverse=True)
    elif sort_by == "name_asc":
        enriched_rows.sort(key=lambda x: x["medicine_name"].lower())
    elif sort_by == "quantity_desc":
        enriched_rows.sort(key=lambda x: x["quantity"], reverse=True)
    elif sort_by == "days_remaining_asc":
        enriched_rows.sort(key=lambda x: x["days_remaining"])

    return enriched_rows


def get_all_manufacturers() -> List[str]:
    """
    Returns unique list of manufacturers present in the database.
    """
    rows = fetch_all("SELECT DISTINCT manufacturer FROM medicines WHERE manufacturer IS NOT NULL ORDER BY manufacturer;")
    return [r["manufacturer"] for r in rows if r["manufacturer"]]


def export_medicines_dataframe(threshold_days: int = DEFAULT_EXPIRING_SOON_DAYS) -> pd.DataFrame:
    """
    Prepares a clean pandas DataFrame of medicines suitable for CSV export and reporting.
    """
    medicines = get_all_medicines(threshold_days=threshold_days)
    if not medicines:
        return pd.DataFrame()

    df = pd.DataFrame(medicines)
    columns_order = [
        "id",
        "medicine_name",
        "generic_name",
        "manufacturer",
        "batch_number",
        "barcode",
        "manufacturing_date",
        "expiry_date",
        "expiry_status",
        "days_remaining",
        "dosage",
        "quantity",
        "unit",
        "notes",
    ]
    present_cols = [c for c in columns_order if c in df.columns]
    return df[present_cols]
