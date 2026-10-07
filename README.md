# MEDISAFE
### *Medicine Expiry, Authenticity and Smart Reminders*
> **"Check. Verify. Remember. Stay Safe."**  
> *B.Tech Computer Science & Engineering Capstone / Final Year Project Prototype*

---

## ⚠️ Academic Prototype & Safety Notice

> **IMPORTANT DISCLAIMER**:  
> MediSafe is an **academic prototype** engineered for medicine record management, inventory tracking, and dosage scheduling.  
> 1. **Stored Date Basis**: Medicine expiry classification is based strictly on dates stored in the database.
> 2. **Verification Scope**: Batch, barcode, and QR verification only verifies whether the identifier exists in the trusted prototype database.
> 3. **Not Medical Guarantee**: A status of **"VERIFIED RECORD FOUND"** does **NOT** guarantee that the physical medicine is authentic, unadulterated, stored under proper temperature/humidity, or medically safe.
> 4. **No Medical Advice**: The system never provides medical diagnosis, treatment advice, or dosage recommendations.
> 5. **User-Entered Dosages**: Dosage information is strictly displayed as entered by the user or sample registry. Always consult a licensed healthcare professional.

---

## 1. Problem Statement
Accidental consumption of expired pharmaceuticals leads to treatment failure, adverse reactions, and toxic by-products. Concurrently, counterfeit drugs in parallel supply chains pose severe global health threats. Furthermore, patients coping with chronic regimens frequently miss or mistime doses, resulting in poor therapeutic outcomes. Existing health tools either focus exclusively on inventory or alarms without linking expiration hazard tracking, packaging identifier validation, and daily adherence history.

## 2. Project Objectives
MediSafe resolves these issues within an integrated academic platform:
1. **Automated Expiry Classification**: Instantly categorizes shelf life into **EXPIRED**, **EXPIRING SOON**, and **VALID** with configurable warning horizons.
2. **Identifier Verification Engine**: Validates Batch Numbers, Barcodes, and QR payloads against a trusted prototype registry with comprehensive audit logging.
3. **Smart Dosage Reminders & History**: Schedules daily, twice-daily, or weekly doses with one-click **Taken** and **Skipped** logging, calculating compliance rates without duplicate slot generation.
4. **Interactive Analytics Dashboard**: Delivers 7 core KPI metrics, Priority Safety Alerts, and Plotly visual analytics for inventory and adherence.
5. **Zero-Configuration SQLite Database**: Boots immediately out-of-the-box with dynamically calculated sample data.

---

## 3. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.10+ | Core application logic and data modeling |
| **User Interface** | Streamlit | Multi-page modern medical dashboard |
| **Database** | SQLite3 | Local embedded relational database with Foreign Keys |
| **Data Processing** | Pandas | Tabular data transformation, filtering & CSV export |
| **Visualizations** | Plotly (Graph Objects & Express) | Interactive charts (Donut, Adherence, Mfg, Expiry) |
| **Identifiers & QR** | QRCode, Pillow (PIL) | Dynamic QR code generation, rendering & PNG download |
| **Scheduling** | APScheduler & Datetime | Dose slot calculation and duplicate prevention |
| **Testing** | Pytest | Comprehensive unit test suite |

---

## 4. System Architecture

```text
                                  ┌────────────────────────┐
                                  │      STUDENT / USER    │
                                  └───────────┬────────────┘
                                              │ (Browser)
                                              ▼
                        ┌─────────────────────────────────────────┐
                        │          STREAMLIT UI LAYER             │
                        │  Dashboard  │  Catalog  │  Checker  ... │
                        └─────────────────────┬───────────────────┘
                                              │
                        ┌─────────────────────▼───────────────────┐
                        │        APPLICATION LOGIC LAYER          │
                        │                                         │
                        │  ├── Medicine Manager (medicine.py)     │
                        │  ├── Expiry Checker (expiry_checker.py) │
                        │  ├── Reminder Manager (reminder.py)     │
                        │  ├── Verification Manager (verify.py)   │
                        │  └── In-App Alerts (notification.py)    │
                        └─────────────────────┬───────────────────┘
                                              │ Parameterized SQL
                                              ▼
                        ┌─────────────────────────────────────────┐
                        │          DATABASE LAYER (SQLite3)       │
                        │              data/medsafe.db            │
                        │  users | medicines | reminders          │
                        │  verification_records | history         │
                        └─────────────────────────────────────────┘
```

---

## 5. Database Schema

The prototype utilizes SQLite with `PRAGMA foreign_keys = ON;` and parameterized queries:

1. **`users`**: Academic prototype user context (`id`, `username`, `full_name`, `created_at`).
2. **`medicines`**: Central pharmaceutical registry:
   - `id`, `user_id`, `medicine_name`, `generic_name`, `manufacturer`, `batch_number` (UNIQUE), `barcode`, `qr_code`, `manufacturing_date`, `expiry_date`, `dosage`, `quantity`, `unit`, `notes`, `created_at`, `updated_at`.
3. **`reminders`**: Dosage frequency schedules:
   - `id`, `medicine_id` (FK CASCADE), `dosage`, `reminder_time`, `frequency`, `start_date`, `end_date`, `status`, `created_at`.
4. **`verification_records`**: Identifier verification audit trail:
   - `id`, `medicine_id` (FK SET NULL), `identifier_type`, `identifier_value`, `verification_status`, `verified_at`.
5. **`medication_history`**: Dose intake compliance log:
   - `id`, `medicine_id` (FK CASCADE), `reminder_id` (FK SET NULL), `scheduled_time`, `actual_time`, `status`, `notes`, `created_at`, `UNIQUE(medicine_id, scheduled_time)` (prevents duplicate daily records).

---

## 6. Directory Structure

```text
MediSafe/
│
├── main.py                     # Primary entrypoint & evaluator guide
├── database.py                 # SQLite connection, schema & dynamic seed data
├── medicine.py                 # Medicine CRUD, search, filter & CSV export
├── expiry_checker.py           # Expiry calculation logic & validation
├── reminder.py                 # Reminder scheduling & dose compliance
├── verification.py             # Identifier verification & QR generator
├── notification.py             # In-app safety alerts aggregator
├── dashboard.py                # 7 KPI metrics & Plotly visual charts
├── utils.py                    # Custom medical CSS, badges & logo generator
├── config.py                   # Constants, paths, and disclaimers
├── requirements.txt            # Python dependencies
├── README.md                   # Complete academic documentation
├── .gitignore                  # Git ignore rules
│
├── data/
│   └── medsafe.db              # Auto-created SQLite database file
│
├── assets/
│   └── logo.png                # Generated MediSafe medical emblem
│
├── pages/
│   ├── 1_Dashboard.py          # Summary KPIs, safety alerts, charts, doses
│   ├── 2_Medicines.py          # Inventory catalog, search, edit, delete, QR
│   ├── 3_Add_Medicine.py       # Register medicine form with date validation
│   ├── 4_Expiry_Checker.py     # Threshold sandbox, countdown, categorized lots
│   ├── 5_Verification.py       # Batch/Barcode/QR lookup, QR generator, audit log
│   ├── 6_Reminders.py          # Create reminder schedules, mark Taken/Skipped
│   └── 7_History.py            # Medication dose history, compliance rate, CSV
│
└── tests/
    ├── test_expiry.py          # Expiry status & date validation unit tests
    ├── test_database.py        # Database schema, CRUD & constraint tests
    └── test_verification.py    # Verification match/mismatch & audit tests
```

---

## 7. Installation & Setup

### Prerequisites
- Python 3.10 or higher
- PowerShell, Terminal, or Command Prompt

### Step 1: Clone or Navigate to the Workspace
```powershell
cd d:\MedicineChecker
```

### Step 2: Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 3: Launching MediSafe

#### Option A: Native Desktop Application (Windowed GUI)
To launch MediSafe as a native standalone desktop window:
```powershell
python desktop_app.py
```
*Or double-click **`run_desktop.bat`** (or **`run_desktop_silent.vbs`** for no terminal window).*

#### Option B: Web Browser Mode
To run inside your default web browser:
```powershell
python -m streamlit run main.py
```
*Accessible at `http://localhost:8501`.*

---

## 8. Evaluator Demonstration Walkthrough

Follow these steps to demonstrate all project capabilities to an examiner or evaluator:

1. **Open the Dashboard (`1_Dashboard.py`)**:
   - Inspect the **7 KPI cards** (Total Medicines, Valid, Expiring Soon, Expired, Today's Reminders, Taken Doses, Skipped Doses).
   - Review the **Priority Safety Alerts** (critical alerts for expired items like *Paracetamol 500mg*).
   - Scroll down to examine the **4 Plotly charts** (Status donut chart, Adherence stack, Manufacturer distribution, and Upcoming Expiry timeline).
2. **Review Inventory & Search (`2_Medicines.py`)**:
   - Filter medicines by **Expiry Status** (`EXPIRED`, `EXPIRING SOON`, `VALID`).
   - Search for `Cipla` or `Amoxicillin`.
   - Expand a medicine card to inspect batch details and click **Download QR**.
   - Click **Export Inventory (CSV)** to download the database.
3. **Register a Medicine (`3_Add_Medicine.py`)**:
   - Fill in:
     - Medicine Name: `Cetirizine 10mg Extra`
     - Manufacturer: `Sun Pharmaceutical Ltd`
     - Batch: `SUN-CET-5588`
     - Mfg Date: (Today - 30 days)
     - Expiry Date: (Today + 180 days)
     - Dosage: `10 mg`, Quantity: `20 Tablets`
   - Notice the live preview calculates `VALID` and generates a QR code before submission.
   - Click **Register Medicine**; verify instant validation and database insertion.
4. **Test Expiry Classification (`4_Expiry_Checker.py`)**:
   - Adjust the **Expiring Soon Alert Threshold** slider from 30 days to 60 days.
   - Notice medicines dynamically reclassify based on the new threshold.
   - Test an arbitrary date in the **Date Checker Simulator**.
5. **Verify Authenticity (`5_Verification.py`)**:
   - Click the **Quick Demo Auto-Fill** to select `SUN-PARA-9821`.
   - Click **Verify Against Registry** -> Returns **VERIFIED RECORD FOUND** with details and disclaimer.
   - Enter a fictional batch `FAKE-LOT-0000` -> Returns **RECORD NOT FOUND**.
   - Check the **Verification Audit Log** tab to see logged attempts.
6. **Track Reminders & Record Doses (`6_Reminders.py`)**:
   - Under **Today's Doses**, click **Mark Taken** on one dose.
   - Click **Mark Skipped** on another dose.
   - Notice the status immediately changes with timestamps.
7. **Inspect Adherence Compliance (`7_History.py`)**:
   - View the overall **Compliance Rate (%)** calculated from taken vs completed doses.
   - Export full dose history as CSV.
8. **Reset Database (Evaluator Tool)**:
   - In the sidebar on `main.py`, click **Reset Demo Database** at any time to reseed clean sample data.

---

## 9. Running the Unit Tests

Execute the full automated test suite using `pytest`:

```powershell
python -m pytest tests/ -v
```

### Expected Output:
```text
tests/test_database.py::test_database_tables_exist PASSED                [  6%]
tests/test_database.py::test_medicine_crud PASSED                        [ 12%]
tests/test_database.py::test_duplicate_batch_number_rejected PASSED      [ 18%]
tests/test_expiry.py::test_expired_medicine PASSED                       [ 25%]
tests/test_expiry.py::test_expiring_soon_medicine PASSED                 [ 31%]
tests/test_expiry.py::test_valid_medicine PASSED                         [ 37%]
tests/test_expiry.py::test_expires_today PASSED                          [ 43%]
tests/test_expiry.py::test_custom_threshold PASSED                       [ 50%]
tests/test_expiry.py::test_mfg_date_after_exp_date_invalid PASSED        [ 56%]
tests/test_expiry.py::test_mfg_date_before_exp_date_valid PASSED         [ 62%]
tests/test_verification.py::test_verification_batch_found PASSED         [ 68%]
tests/test_verification.py::test_verification_barcode_found PASSED       [ 75%]
tests/test_verification.py::test_verification_qr_string_found PASSED     [ 81%]
tests/test_verification.py::test_verification_not_found PASSED           [ 87%]
tests/test_verification.py::test_verification_empty_requires_input PASSED [ 93%]
tests/test_verification.py::test_verification_audit_logged PASSED        [100%]
============================= 16 passed in 1.44s ==============================
```

---

## 10. System Limitations
1. **Academic Database Scope**: Identifier verification only matches against the prototype SQLite database; it cannot detect counterfeit chemicals physically placed in genuine packaging.
2. **Date Reliant**: Shelf life relies on user-provided dates and does not monitor environmental sensors (temperature, humidity, sunlight).
3. **In-App Notifications**: Alerts are presented within the application interface; external SMS/WhatsApp gateways are intentionally omitted to avoid misleading evaluators.

---

## 11. Future Scope
* **Native Mobile Application (Android/iOS)**: Direct smartphone camera scanning of 1D/2D GS1 DataMatrix barcodes and QR codes.
* **National Pharmaceutical API Integration**: Live federation with government drug authentication databases (e.g., FDA, CDSCO portal).
* **IoT Smart Medicine Cabinet**: BLE/WiFi sensor integration to monitor temperature, humidity, and pill container opening events.
* **Caregiver & Family Alerts**: Automated push notifications to designated caregivers if critical doses remain unconfirmed past grace windows.
* **AI Prescription-to-Schedule Parser**: OCR and LLM extraction of prescribed dosage schedules directly from photographed doctor slips.

---

## 12. Project Metadata
- **Project Name**: MEDISAFE
- **Degree**: Bachelor of Technology (B.Tech) in Computer Science & Engineering
- **Focus Area**: Healthcare Informatics, Relational Data Systems, Software Engineering
- **Version**: 1.0.0
