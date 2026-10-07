"""
MediSafe - In-App Notification Module
Aggregates safety alerts, expiry warnings, and upcoming medication doses.
Transparently implements an in-app notification center without pretending
to send external SMS/WhatsApp messages.
"""

from typing import Any, Dict, List
from medicine import get_all_medicines
from reminder import get_today_doses
from config import STATUS_EXPIRED, STATUS_EXPIRING_SOON, DOSE_PENDING


def get_active_alerts(threshold_days: int = 30) -> Dict[str, List[Dict[str, Any]]]:
    """
    Scans the database and collates priority alerts into categories:
    - critical: Expired medicines (safety hazard)
    - warnings: Medicines expiring within threshold_days
    - reminders: Pending medication doses for today
    """
    medicines = get_all_medicines(threshold_days=threshold_days)
    today_doses = get_today_doses()

    critical_alerts = []
    warning_alerts = []
    reminder_alerts = []

    for med in medicines:
        if med["expiry_status"] == STATUS_EXPIRED:
            critical_alerts.append({
                "type": "EXPIRED_MEDICINE",
                "severity": "CRITICAL",
                "title": f"Expired: {med['medicine_name']}",
                "message": f"Expired on {med['expiry_date']} ({med['expiry_message']}). Do not consume.",
                "batch": med["batch_number"],
                "medicine_id": med["id"],
            })
        elif med["expiry_status"] == STATUS_EXPIRING_SOON:
            warning_alerts.append({
                "type": "EXPIRING_SOON",
                "severity": "WARNING",
                "title": f"Expiring Soon: {med['medicine_name']}",
                "message": f"{med['expiry_message']} (Expires: {med['expiry_date']}). Check remaining stock.",
                "batch": med["batch_number"],
                "medicine_id": med["id"],
            })

    for dose in today_doses:
        if dose["status"] == DOSE_PENDING:
            reminder_alerts.append({
                "type": "PENDING_DOSE",
                "severity": "INFO",
                "title": f"Due Dose: {dose['medicine_name']} ({dose['dosage']})",
                "message": f"Scheduled for today at {dose['scheduled_time'].split(' ')[1][:5]}.",
                "history_id": dose["history_id"],
                "medicine_id": dose["medicine_id"],
            })

    return {
        "critical": critical_alerts,
        "warnings": warning_alerts,
        "reminders": reminder_alerts,
        "total_count": len(critical_alerts) + len(warning_alerts) + len(reminder_alerts),
    }
