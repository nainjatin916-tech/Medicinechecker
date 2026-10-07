"""
MediSafe - Database Layer
SQLite connection management, table schemas, parameterized operations,
and sample dataset seeding for B.Tech CSE evaluation.
"""

import sqlite3
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from config import (
    DATABASE_PATH,
    STATUS_EXPIRED,
    STATUS_EXPIRING_SOON,
    STATUS_VALID,
    DOSE_TAKEN,
    DOSE_SKIPPED,
    DOSE_PENDING,
    FREQUENCY_DAILY,
    FREQUENCY_TWICE_DAILY,
    FREQUENCY_ONCE,
    VERIFIED_FOUND,
)


from contextlib import contextmanager


@contextmanager
def get_db_connection():
    """
    Creates and yields a SQLite connection with foreign keys enabled
    and row factory set to sqlite3.Row for dict-like access.
    Guarantees the connection is closed upon exit to prevent lock issues on Windows.
    """
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database() -> None:
    """
    Initializes the database schema if tables do not exist,
    and seeds sample data if the medicines table is empty.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Users table (for academic prototype user context)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)

        # 2. Medicines table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                medicine_name TEXT NOT NULL,
                generic_name TEXT,
                manufacturer TEXT NOT NULL,
                batch_number TEXT NOT NULL UNIQUE,
                barcode TEXT,
                qr_code TEXT,
                manufacturing_date TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                dosage TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
        """)

        # 3. Reminders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_id INTEGER NOT NULL,
                dosage TEXT NOT NULL,
                reminder_time TEXT NOT NULL,
                frequency TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT DEFAULT 'ACTIVE',
                created_at TEXT NOT NULL,
                FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
            );
        """)

        # 4. Verification Records table (audit log)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_id INTEGER,
                identifier_type TEXT NOT NULL,
                identifier_value TEXT NOT NULL,
                verification_status TEXT NOT NULL,
                verified_at TEXT NOT NULL,
                FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE SET NULL
            );
        """)

        # 5. Medication History table (dose tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medication_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_id INTEGER NOT NULL,
                reminder_id INTEGER,
                scheduled_time TEXT NOT NULL,
                actual_time TEXT,
                status TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(medicine_id, scheduled_time),
                FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE,
                FOREIGN KEY (reminder_id) REFERENCES reminders(id) ON DELETE SET NULL
            );
        """)

        conn.commit()

    # Seed sample data if empty
    seed_sample_data_if_needed()


def seed_sample_data_if_needed() -> None:
    """
    Inserts realistic sample medicines, reminders, and dose records
    if the database has no medicines yet.
    Dates are computed dynamically relative to today's date so that
    the demo always has expired, expiring soon, and valid items.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check default user
        cursor.execute("SELECT id FROM users WHERE id = 1;")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (id, username, full_name, created_at) VALUES (1, 'student_demo', 'B.Tech Prototype User', ?);",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),),
            )

        # Check if medicines already exist
        cursor.execute("SELECT COUNT(*) FROM medicines;")
        count = cursor.fetchone()[0]
        if count > 0:
            return  # Already seeded

        today = date.today()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Define 12 realistic sample medicines spanning Expired, Expiring Soon, and Valid
        sample_medicines = [
            # Expired medicines
            {
                "name": "Paracetamol 500mg",
                "generic": "Acetaminophen",
                "mfg": "Sun Pharmaceutical Ltd",
                "batch": "SUN-PARA-9821",
                "barcode": "8901030101112",
                "qr": "MEDISAFE|BATCH:SUN-PARA-9821|BARCODE:8901030101112",
                "mfg_date": (today - timedelta(days=730)).strftime("%Y-%m-%d"),
                "exp_date": (today - timedelta(days=45)).strftime("%Y-%m-%d"),
                "dosage": "500 mg",
                "quantity": 20,
                "unit": "Tablets",
                "notes": "Stored in medicine cabinet. DO NOT CONSUME - past expiry.",
            },
            {
                "name": "Amoxicillin Trihydrate 250mg",
                "generic": "Amoxicillin",
                "mfg": "Cipla Ltd",
                "batch": "CIP-AMOX-4412",
                "barcode": "8901030102223",
                "qr": "MEDISAFE|BATCH:CIP-AMOX-4412|BARCODE:8901030102223",
                "mfg_date": (today - timedelta(days=500)).strftime("%Y-%m-%d"),
                "exp_date": (today - timedelta(days=15)).strftime("%Y-%m-%d"),
                "dosage": "250 mg",
                "quantity": 10,
                "unit": "Capsules",
                "notes": "Antibiotic course from last illness. Expired.",
            },
            {
                "name": "Cetirizine Hydrochloride 10mg",
                "generic": "Cetirizine",
                "mfg": "Dr. Reddy's Laboratories",
                "batch": "RED-CET-3190",
                "barcode": "8901030103334",
                "qr": "MEDISAFE|BATCH:RED-CET-3190|BARCODE:8901030103334",
                "mfg_date": (today - timedelta(days=600)).strftime("%Y-%m-%d"),
                "exp_date": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
                "dosage": "10 mg",
                "quantity": 15,
                "unit": "Tablets",
                "notes": "Antihistamine for seasonal allergies.",
            },
            # Expiring Soon medicines (within 30 days)
            {
                "name": "Azithromycin 500mg",
                "generic": "Azithromycin",
                "mfg": "Torrent Pharmaceuticals",
                "batch": "TOR-AZI-7719",
                "barcode": "8901030104445",
                "qr": "MEDISAFE|BATCH:TOR-AZI-7719|BARCODE:8901030104445",
                "mfg_date": (today - timedelta(days=340)).strftime("%Y-%m-%d"),
                "exp_date": (today + timedelta(days=6)).strftime("%Y-%m-%d"),
                "dosage": "500 mg",
                "quantity": 3,
                "unit": "Tablets",
                "notes": "Expiring in less than a week. Finish or dispose.",
            },
            {
                "name": "Omeprazole 20mg",
                "generic": "Omeprazole",
                "mfg": "Lupin Limited",
                "batch": "LUP-OME-5520",
                "barcode": "8901030105556",
                "qr": "MEDISAFE|BATCH:LUP-OME-5520|BARCODE:8901030105556",
                "mfg_date": (today - timedelta(days=350)).strftime("%Y-%m-%d"),
                "exp_date": (today + timedelta(days=14)).strftime("%Y-%m-%d"),
                "dosage": "20 mg",
                "quantity": 14,
                "unit": "Capsules",
                "notes": "For acidity / gastric reflux. Morning dose before food.",
            },
            {
                "name": "Ibuprofen 400mg",
                "generic": "Ibuprofen",
                "mfg": "Abbott India",
                "batch": "ABB-IBU-1120",
                "barcode": "8901030106667",
                "qr": "MEDISAFE|BATCH:ABB-IBU-1120|BARCODE:8901030106667",
                "mfg_date": (today - timedelta(days=330)).strftime("%Y-%m-%d"),
                "exp_date": (today + timedelta(days=22)).strftime("%Y-%m-%d"),
                "dosage": "400 mg",
                "quantity": 8,
                "unit": "Tablets",
                "notes": "Pain reliever and anti-inflammatory.",
            },
            # Valid medicines (safe future expiry)
            {
                "name": "Metformin Hydrochloride 500mg",
                "generic": "Metformin",
                "mfg": "Sun Pharmaceutical Ltd",
                "batch": "SUN-MET-8841",
                "barcode": "8901030107778",
                "qr": "MEDISAFE|BATCH:SUN-MET-8841|BARCODE:8901030107778",
                "mfg_date": (today - timedelta(days=60)).strftime("%Y-%m-%d"),
                "exp_date": (today + timedelta(days=365)).strftime("%Y-%m-%d"),
                "dosage": "500 mg",
                "quantity": 60,
                "unit": "Tablets",
                "notes": "Regular blood sugar maintenance medication.",
            },
            {
                "name": "Atorvastatin 10mg",
                "generic": "Atorvastatin Calcium",
                "mfg": "Cipla Ltd",
                "batch": "CIP-ATO-3390",
                "barcode": "8901030108889",
                "qr": "MEDISAFE|BATCH:CIP-ATO-3390|BARCODE:8901030108889",
                "mfg_date": (today - timedelta(days=90)).strftime("%Y-%m-%d"),
                "exp_date": (today + timedelta(days=270)).strftime("%Y-%m-%d"),
                "dosage": "10 mg",
                "quantity": 30,
                "unit": "Tablets",
                "notes": "Cholesterol regulation. Take at bedtime.",
            },
            {
                "name": "Pantoprazole 40mg",
                "generic": "Pantoprazole Sodium",
                "mfg": "Dr. Reddy's Laboratories",
                "batch": "RED-PAN-6623",
                "barcode": "8901030109990",
                "qr": "MEDISAFE|BATCH:RED-PAN-6623|BARCODE:8901030109990",
                "mfg_date": (today - timedelta(days=40)).strftime("%Y-%m-%d"),
                "exp_date": (today + timedelta(days=450)).strftime("%Y-%m-%d"),
                "dosage": "40 mg",
                "quantity": 28,
                "unit": "Tablets",
                "notes": "Proton pump inhibitor.",
            },
            {
                "name": "Cholecalciferol 60,000 IU",
                "generic": "Vitamin D3",
                "mfg": "Torrent Pharmaceuticals",
                "batch": "TOR-VIT-9934",
                "barcode": "8901030110001",
                "qr": "MEDISAFE|BATCH:TOR-VIT-9934|BARCODE:8901030110001",
                "mfg_date": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
                "exp_date": (today + timedelta(days=550)).strftime("%Y-%m-%d"),
                "dosage": "60000 IU",
                "quantity": 4,
                "unit": "Capsules",
                "notes": "Weekly vitamin D supplement.",
            },
            {
                "name": "Montelukast 10mg",
                "generic": "Montelukast Sodium",
                "mfg": "Lupin Limited",
                "batch": "LUP-MON-2218",
                "barcode": "8901030111112",
                "qr": "MEDISAFE|BATCH:LUP-MON-2218|BARCODE:8901030111112",
                "mfg_date": (today - timedelta(days=50)).strftime("%Y-%m-%d"),
                "exp_date": (today + timedelta(days=300)).strftime("%Y-%m-%d"),
                "dosage": "10 mg",
                "quantity": 20,
                "unit": "Tablets",
                "notes": "Respiratory allergy prophylaxis.",
            },
            {
                "name": "Telmisartan 40mg",
                "generic": "Telmisartan",
                "mfg": "Abbott India",
                "batch": "ABB-TEL-7744",
                "barcode": "8901030112223",
                "qr": "MEDISAFE|BATCH:ABB-TEL-7744|BARCODE:8901030112223",
                "mfg_date": (today - timedelta(days=20)).strftime("%Y-%m-%d"),
                "exp_date": (today + timedelta(days=600)).strftime("%Y-%m-%d"),
                "dosage": "40 mg",
                "quantity": 30,
                "unit": "Tablets",
                "notes": "Blood pressure management.",
            },
        ]

        inserted_medicine_ids = []
        for med in sample_medicines:
            cursor.execute(
                """
                INSERT INTO medicines (
                    user_id, medicine_name, generic_name, manufacturer, batch_number,
                    barcode, qr_code, manufacturing_date, expiry_date, dosage,
                    quantity, unit, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    1,
                    med["name"],
                    med["generic"],
                    med["mfg"],
                    med["batch"],
                    med["barcode"],
                    med["qr"],
                    med["mfg_date"],
                    med["exp_date"],
                    med["dosage"],
                    med["quantity"],
                    med["unit"],
                    med["notes"],
                    now_str,
                    now_str,
                ),
            )
            inserted_medicine_ids.append(cursor.lastrowid)

        # Seed sample reminders
        # Reminder 1: Metformin (Daily 08:30)
        # Reminder 2: Atorvastatin (Daily 21:00)
        # Reminder 3: Omeprazole (Daily 07:30)
        # Reminder 4: Cholecalciferol (Weekly 10:00)
        reminders_data = [
            {
                "med_id": inserted_medicine_ids[6],  # Metformin
                "dosage": "500 mg",
                "time": "08:30",
                "freq": FREQUENCY_DAILY,
                "start": (today - timedelta(days=14)).strftime("%Y-%m-%d"),
                "end": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            },
            {
                "med_id": inserted_medicine_ids[7],  # Atorvastatin
                "dosage": "10 mg",
                "time": "21:00",
                "freq": FREQUENCY_DAILY,
                "start": (today - timedelta(days=14)).strftime("%Y-%m-%d"),
                "end": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            },
            {
                "med_id": inserted_medicine_ids[4],  # Omeprazole
                "dosage": "20 mg",
                "time": "07:30",
                "freq": FREQUENCY_DAILY,
                "start": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
                "end": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
            },
            {
                "med_id": inserted_medicine_ids[9],  # Vitamin D3
                "dosage": "60000 IU",
                "time": "10:00",
                "freq": FREQUENCY_ONCE,
                "start": today.strftime("%Y-%m-%d"),
                "end": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            },
        ]

        inserted_reminder_ids = []
        for rem in reminders_data:
            cursor.execute(
                """
                INSERT INTO reminders (
                    medicine_id, dosage, reminder_time, frequency, start_date, end_date, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', ?);
                """,
                (
                    rem["med_id"],
                    rem["dosage"],
                    rem["time"],
                    rem["freq"],
                    rem["start"],
                    rem["end"],
                    now_str,
                ),
            )
            inserted_reminder_ids.append(cursor.lastrowid)

        # Seed sample medication history
        # Create past doses (Taken, Skipped) and Today's dose (Taken / Pending)
        history_records = [
            # Metformin: Yesterday morning (Taken)
            (
                inserted_medicine_ids[6],
                inserted_reminder_ids[0],
                f"{(today - timedelta(days=1)).strftime('%Y-%m-%d')} 08:30:00",
                f"{(today - timedelta(days=1)).strftime('%Y-%m-%d')} 08:35:12",
                DOSE_TAKEN,
                "Taken after breakfast with warm water.",
                now_str,
            ),
            # Metformin: Today morning (Taken)
            (
                inserted_medicine_ids[6],
                inserted_reminder_ids[0],
                f"{today.strftime('%Y-%m-%d')} 08:30:00",
                f"{today.strftime('%Y-%m-%d')} 08:32:05",
                DOSE_TAKEN,
                "Taken on time.",
                now_str,
            ),
            # Atorvastatin: Yesterday night (Taken)
            (
                inserted_medicine_ids[7],
                inserted_reminder_ids[1],
                f"{(today - timedelta(days=1)).strftime('%Y-%m-%d')} 21:00:00",
                f"{(today - timedelta(days=1)).strftime('%Y-%m-%d')} 21:04:40",
                DOSE_TAKEN,
                "Night bedtime dose.",
                now_str,
            ),
            # Omeprazole: Yesterday morning (Skipped)
            (
                inserted_medicine_ids[4],
                inserted_reminder_ids[2],
                f"{(today - timedelta(days=1)).strftime('%Y-%m-%d')} 07:30:00",
                None,
                DOSE_SKIPPED,
                "Fasting required for blood tests.",
                now_str,
            ),
            # Omeprazole: Today morning (Pending)
            (
                inserted_medicine_ids[4],
                inserted_reminder_ids[2],
                f"{today.strftime('%Y-%m-%d')} 07:30:00",
                None,
                DOSE_PENDING,
                "Scheduled morning dose.",
                now_str,
            ),
            # Atorvastatin: Today night (Pending)
            (
                inserted_medicine_ids[7],
                inserted_reminder_ids[1],
                f"{today.strftime('%Y-%m-%d')} 21:00:00",
                None,
                DOSE_PENDING,
                "Upcoming tonight.",
                now_str,
            ),
        ]

        for h in history_records:
            cursor.execute(
                """
                INSERT OR IGNORE INTO medication_history (
                    medicine_id, reminder_id, scheduled_time, actual_time, status, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                h,
            )

        # Seed sample verification audit records
        sample_verifications = [
            (
                inserted_medicine_ids[0],
                "Batch Number",
                "SUN-PARA-9821",
                VERIFIED_FOUND,
                (today - timedelta(days=2)).strftime("%Y-%m-%d 14:15:00"),
            ),
            (
                inserted_medicine_ids[6],
                "Barcode",
                "8901030107778",
                VERIFIED_FOUND,
                (today - timedelta(days=1)).strftime("%Y-%m-%d 11:20:00"),
            ),
            (
                None,
                "Batch Number",
                "FAKE-XYZ-9999",
                "RECORD NOT FOUND",
                (today - timedelta(days=1)).strftime("%Y-%m-%d 16:45:00"),
            ),
        ]

        for v in sample_verifications:
            cursor.execute(
                """
                INSERT INTO verification_records (
                    medicine_id, identifier_type, identifier_value, verification_status, verified_at
                ) VALUES (?, ?, ?, ?, ?);
                """,
                v,
            )

        conn.commit()


def reset_database() -> None:
    """
    Drops existing tables and reseeds fresh sample data.
    Useful for demonstration resets.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS medication_history;")
        cursor.execute("DROP TABLE IF EXISTS verification_records;")
        cursor.execute("DROP TABLE IF EXISTS reminders;")
        cursor.execute("DROP TABLE IF EXISTS medicines;")
        cursor.execute("DROP TABLE IF EXISTS users;")
        conn.commit()
    init_database()


def execute_query(sql: str, params: Tuple[Any, ...] = ()) -> int:
    """
    Executes a write query (INSERT, UPDATE, DELETE) with parameters.
    Returns the lastrowid or rowcount.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid if cursor.lastrowid else cursor.rowcount


def fetch_all(sql: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
    """
    Executes a SELECT query with parameters and returns a list of dictionaries.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def fetch_one(sql: str, params: Tuple[Any, ...] = ()) -> Optional[Dict[str, Any]]:
    """
    Executes a SELECT query with parameters and returns a single dictionary or None.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None
