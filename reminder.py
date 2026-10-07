"""
MediSafe - Reminder & Dose Tracking Module
Manages medication schedules, upcoming reminders, dose tracking (Taken, Skipped, Pending),
and dose history logging with duplicate prevention.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from database import execute_query, fetch_all, fetch_one
from config import (
    DOSE_TAKEN,
    DOSE_SKIPPED,
    DOSE_PENDING,
    FREQUENCY_ONCE,
    FREQUENCY_DAILY,
    FREQUENCY_TWICE_DAILY,
    FREQUENCY_WEEKLY,
)


def create_reminder(
    medicine_id: int,
    dosage: str,
    reminder_time: str,
    frequency: str,
    start_date: str,
    end_date: str,
) -> Tuple[bool, str, Optional[int]]:
    """
    Creates a new medication reminder schedule in SQLite.
    Validates dates and parameters.
    """
    if not medicine_id:
        return False, "Medicine selection is required.", None
    if not dosage.strip():
        return False, "Dosage is required.", None
    if not reminder_time.strip():
        return False, "Reminder time is required.", None
    if not start_date or not end_date:
        return False, "Start and end dates are required.", None

    try:
        s_date = datetime.strptime(str(start_date).split(" ")[0], "%Y-%m-%d").date()
        e_date = datetime.strptime(str(end_date).split(" ")[0], "%Y-%m-%d").date()
        if s_date > e_date:
            return False, "Start date cannot be after end date.", None
    except ValueError as e:
        return False, f"Invalid date format: {str(e)}", None

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_time = reminder_time.strip()
    if len(clean_time) == 5:
        # e.g., "08:30"
        clean_time = f"{clean_time}:00"

    sql = """
        INSERT INTO reminders (
            medicine_id, dosage, reminder_time, frequency, start_date, end_date, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', ?);
    """
    params = (
        medicine_id,
        dosage.strip(),
        clean_time[:5],
        frequency,
        str(s_date),
        str(e_date),
        now_str,
    )

    try:
        rem_id = execute_query(sql, params)
        # Immediately generate today's dose slot if applicable
        generate_today_dose_instances()
        return True, "Reminder successfully created.", rem_id
    except Exception as e:
        return False, f"Database error: {str(e)}", None


def delete_reminder(reminder_id: int) -> Tuple[bool, str]:
    """
    Deletes a reminder.
    """
    try:
        execute_query("DELETE FROM reminders WHERE id = ?;", (reminder_id,))
        return True, "Reminder deleted successfully."
    except Exception as e:
        return False, f"Database error: {str(e)}"


def get_all_reminders() -> List[Dict[str, Any]]:
    """
    Returns all reminders joined with medicine details.
    """
    sql = """
        SELECT
            r.*,
            m.medicine_name,
            m.manufacturer,
            m.batch_number,
            m.expiry_date
        FROM reminders r
        JOIN medicines m ON r.medicine_id = m.id
        ORDER BY r.reminder_time ASC;
    """
    return fetch_all(sql)


def generate_today_dose_instances() -> None:
    """
    Ensures dose history records exist for all active reminders for today.
    Uses SQLite UNIQUE(medicine_id, scheduled_time) with INSERT OR IGNORE
    to prevent duplicate dose-history records.
    """
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Fetch active reminders where today falls within start_date and end_date
    sql = """
        SELECT r.*, m.medicine_name
        FROM reminders r
        JOIN medicines m ON r.medicine_id = m.id
        WHERE r.status = 'ACTIVE'
          AND r.start_date <= ?
          AND r.end_date >= ?;
    """
    active_reminders = fetch_all(sql, (today_str, today_str))

    for rem in active_reminders:
        freq = rem["frequency"]
        r_time_raw = str(rem["reminder_time"]).strip()
        r_time_clean = r_time_raw[:5] if len(r_time_raw) >= 5 else "08:00"
        med_id = rem["medicine_id"]
        rem_id = rem["id"]

        scheduled_times: List[str] = []

        if freq == FREQUENCY_DAILY:
            scheduled_times.append(f"{today_str} {r_time_clean}:00")

        elif freq == FREQUENCY_TWICE_DAILY:
            # Slot 1 at specified time
            scheduled_times.append(f"{today_str} {r_time_clean}:00")
            # Slot 2 (e.g. ~10-12 hours later, staying within today)
            try:
                base_dt = datetime.strptime(f"{today_str} {r_time_clean}", "%Y-%m-%d %H:%M")
                second_dt = base_dt + timedelta(hours=10)
                if second_dt.date() == today:
                    scheduled_times.append(second_dt.strftime("%Y-%m-%d %H:%M:00"))
                else:
                    scheduled_times.append(f"{today_str} 20:00:00")
            except Exception:
                scheduled_times.append(f"{today_str} 20:00:00")

        elif freq == FREQUENCY_ONCE:
            if rem["start_date"] == today_str:
                scheduled_times.append(f"{today_str} {r_time_clean}:00")

        elif freq == FREQUENCY_WEEKLY:
            # Check if today's weekday matches start_date's weekday
            try:
                s_date = datetime.strptime(rem["start_date"], "%Y-%m-%d").date()
                if s_date.weekday() == today.weekday():
                    scheduled_times.append(f"{today_str} {r_time_clean}:00")
            except Exception:
                pass

        # Insert scheduled slots if not already in medication_history
        for s_time in scheduled_times:
            execute_query(
                """
                INSERT OR IGNORE INTO medication_history (
                    medicine_id, reminder_id, scheduled_time, actual_time, status, notes, created_at
                ) VALUES (?, ?, ?, NULL, ?, 'Scheduled dose for today', ?);
                """,
                (med_id, rem_id, s_time, DOSE_PENDING, now_str),
            )


def get_today_doses() -> List[Dict[str, Any]]:
    """
    Returns dose records scheduled for today, joined with medicine details.
    """
    generate_today_dose_instances()
    today_str = date.today().strftime("%Y-%m-%d")

    sql = """
        SELECT
            h.id AS history_id,
            h.medicine_id,
            h.reminder_id,
            h.scheduled_time,
            h.actual_time,
            h.status,
            h.notes,
            m.medicine_name,
            m.dosage,
            m.unit,
            m.manufacturer,
            m.batch_number,
            r.frequency
        FROM medication_history h
        JOIN medicines m ON h.medicine_id = m.id
        LEFT JOIN reminders r ON h.reminder_id = r.id
        WHERE h.scheduled_time LIKE ?
        ORDER BY h.scheduled_time ASC;
    """
    return fetch_all(sql, (f"{today_str}%",))


def mark_dose_status(history_id: int, new_status: str, notes: str = "") -> Tuple[bool, str]:
    """
    Updates the status of a dose to TAKEN or SKIPPED, recording the actual timestamp.
    """
    if new_status not in [DOSE_TAKEN, DOSE_SKIPPED, DOSE_PENDING]:
        return False, f"Invalid dose status: {new_status}"

    actual_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if new_status != DOSE_PENDING else None

    sql = """
        UPDATE medication_history
        SET status = ?, actual_time = ?, notes = CASE WHEN ? != '' THEN ? ELSE notes END
        WHERE id = ?;
    """
    try:
        execute_query(sql, (new_status, actual_time, notes, notes, history_id))
        return True, f"Dose marked as {new_status}."
    except Exception as e:
        return False, f"Database error: {str(e)}"


def get_medication_history(
    status_filter: str = "ALL",
    medicine_filter: Optional[int] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Fetches comprehensive medication history with optional status and medicine filters.
    """
    sql = """
        SELECT
            h.id,
            h.scheduled_time,
            h.actual_time,
            h.status,
            h.notes,
            m.medicine_name,
            m.dosage,
            m.unit,
            m.manufacturer,
            m.batch_number
        FROM medication_history h
        JOIN medicines m ON h.medicine_id = m.id
        WHERE 1=1
    """
    params: List[Any] = []

    if status_filter and status_filter != "ALL":
        sql += " AND h.status = ?"
        params.append(status_filter)

    if medicine_filter:
        sql += " AND h.medicine_id = ?"
        params.append(medicine_filter)

    sql += " ORDER BY h.scheduled_time DESC LIMIT ?;"
    params.append(limit)

    return fetch_all(sql, tuple(params))
