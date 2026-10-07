"""
MediSafe - Verification Module
Medicine identifier verification against the trusted prototype database,
audit logging, and QR code generation.
"""

import io
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from database import execute_query, fetch_all, fetch_one
from expiry_checker import evaluate_medicine_expiry
from config import (
    VERIFIED_FOUND,
    NOT_FOUND,
    VERIFICATION_REQUIRED,
    VERIFICATION_DISCLAIMER,
    IDENTIFIER_BATCH,
    IDENTIFIER_BARCODE,
    IDENTIFIER_QR,
)


def verify_identifier(identifier_type: str, identifier_value: str) -> Dict[str, Any]:
    """
    Verifies a medicine identifier against the prototype database.

    Returns a structured dictionary:
        {
            "status": "VERIFIED RECORD FOUND" | "RECORD NOT FOUND" | "VERIFICATION REQUIRED",
            "medicine": dict or None,
            "message": str,
            "disclaimer": str,
            "identifier_type": str,
            "identifier_value": str,
            "timestamp": str
        }
    """
    clean_val = str(identifier_value).strip() if identifier_value else ""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # If empty or not provided
    if not clean_val:
        return {
            "status": VERIFICATION_REQUIRED,
            "medicine": None,
            "message": "Please enter or scan a valid identifier (Batch Number, Barcode, or QR Code).",
            "disclaimer": VERIFICATION_DISCLAIMER,
            "identifier_type": identifier_type,
            "identifier_value": "",
            "timestamp": now_str,
        }

    medicine_row: Optional[Dict[str, Any]] = None

    if identifier_type == IDENTIFIER_BATCH:
        medicine_row = fetch_one(
            "SELECT * FROM medicines WHERE UPPER(batch_number) = UPPER(?);",
            (clean_val,),
        )
    elif identifier_type == IDENTIFIER_BARCODE:
        medicine_row = fetch_one(
            "SELECT * FROM medicines WHERE barcode = ?;",
            (clean_val,),
        )
    elif identifier_type == IDENTIFIER_QR:
        # Check direct qr_code column or batch/barcode substring match
        medicine_row = fetch_one(
            "SELECT * FROM medicines WHERE qr_code = ? OR UPPER(batch_number) = UPPER(?) OR barcode = ?;",
            (clean_val, clean_val, clean_val),
        )
        # If QR contains pipe-separated string like MEDISAFE|BATCH:XYZ
        if not medicine_row and "BATCH:" in clean_val.upper():
            try:
                parts = clean_val.split("|")
                for part in parts:
                    if part.upper().startswith("BATCH:"):
                        extracted_batch = part.split(":", 1)[1].strip()
                        medicine_row = fetch_one(
                            "SELECT * FROM medicines WHERE UPPER(batch_number) = UPPER(?);",
                            (extracted_batch,),
                        )
                        break
            except Exception:
                pass
    else:
        # Global fallback: check any identifier
        medicine_row = fetch_one(
            "SELECT * FROM medicines WHERE UPPER(batch_number) = UPPER(?) OR barcode = ? OR qr_code = ?;",
            (clean_val, clean_val, clean_val),
        )

    # Determine status and message
    if medicine_row:
        enriched_med = evaluate_medicine_expiry(medicine_row)
        status = VERIFIED_FOUND
        med_id = enriched_med["id"]
        message = (
            f"Matching record found for '{enriched_med['medicine_name']}' "
            f"(Manufacturer: {enriched_med['manufacturer']}, Batch: {enriched_med['batch_number']})."
        )
    else:
        enriched_med = None
        status = NOT_FOUND
        med_id = None
        message = (
            f"No matching medicine record exists in the prototype database for {identifier_type}: '{clean_val}'."
        )

    # Log to verification_records audit log
    try:
        execute_query(
            """
            INSERT INTO verification_records (
                medicine_id, identifier_type, identifier_value, verification_status, verified_at
            ) VALUES (?, ?, ?, ?, ?);
            """,
            (med_id, identifier_type, clean_val, status, now_str),
        )
    except Exception as e:
        # Logging error should not break verification flow
        pass

    return {
        "status": status,
        "medicine": enriched_med,
        "message": message,
        "disclaimer": VERIFICATION_DISCLAIMER,
        "identifier_type": identifier_type,
        "identifier_value": clean_val,
        "timestamp": now_str,
    }


def get_verification_history(limit: int = 50) -> list:
    """
    Fetches the recent verification audit log joined with medicine names.
    """
    sql = """
        SELECT
            v.id,
            v.identifier_type,
            v.identifier_value,
            v.verification_status,
            v.verified_at,
            m.medicine_name,
            m.batch_number,
            m.manufacturer
        FROM verification_records v
        LEFT JOIN medicines m ON v.medicine_id = m.id
        ORDER BY v.id DESC
        LIMIT ?;
    """
    return fetch_all(sql, (limit,))


def generate_qr_image(payload_text: str):
    """
    Generates a QR code image using the qrcode library.
    Returns a PIL Image object, or None if qrcode is unavailable.
    """
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(payload_text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0A2540", back_color="white")
        return img
    except Exception:
        # Fallback or error
        return None


def get_qr_image_bytes(payload_text: str) -> Optional[bytes]:
    """
    Returns the QR code image encoded as PNG bytes.
    """
    img = generate_qr_image(payload_text)
    if img:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    return None
