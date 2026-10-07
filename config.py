"""
MediSafe - Configuration Module
Academic Prototype Configuration and Constants.
"""

from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
DATABASE_PATH = DATA_DIR / "medsafe.db"
LOGO_PATH = ASSETS_DIR / "logo.png"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Application Branding
APP_NAME = "MEDISAFE"
APP_SUBTITLE = "Medicine Expiry, Authenticity and Smart Reminders"
APP_TAGLINE = "Check. Verify. Remember. Stay Safe."
APP_VERSION = "1.0.0 (B.Tech CSE Academic Prototype)"

# Academic Prototype Disclaimer
ACADEMIC_DISCLAIMER = (
    "MediSafe is an academic prototype for medicine record management. "
    "Expiry and identifier checks are based strictly on stored database information. "
    "A verification match does NOT guarantee physical authenticity, chemical quality, "
    "storage conditions, or medical safety. The system never provides medical diagnosis, "
    "treatment recommendations, or dosage advice. Always follow advice from a qualified healthcare professional."
)

# Expiry Constants
DEFAULT_EXPIRING_SOON_DAYS = 30
STATUS_EXPIRED = "EXPIRED"
STATUS_EXPIRING_SOON = "EXPIRING SOON"
STATUS_VALID = "VALID"

# Verification Constants
VERIFIED_FOUND = "VERIFIED RECORD FOUND"
NOT_FOUND = "RECORD NOT FOUND"
VERIFICATION_REQUIRED = "VERIFICATION REQUIRED"

VERIFICATION_DISCLAIMER = (
    "Prototype verification only: a database match does not guarantee physical "
    "authenticity, quality, storage condition, or medical safety."
)

# Dose Tracking Statuses
DOSE_TAKEN = "TAKEN"
DOSE_SKIPPED = "SKIPPED"
DOSE_PENDING = "PENDING"

# Reminder Frequencies
FREQUENCY_ONCE = "Once"
FREQUENCY_DAILY = "Daily"
FREQUENCY_TWICE_DAILY = "Twice Daily"
FREQUENCY_WEEKLY = "Weekly"

FREQUENCIES = [
    FREQUENCY_ONCE,
    FREQUENCY_DAILY,
    FREQUENCY_TWICE_DAILY,
    FREQUENCY_WEEKLY,
]

# Supported Identifier Types
IDENTIFIER_BATCH = "Batch Number"
IDENTIFIER_BARCODE = "Barcode"
IDENTIFIER_QR = "QR Code"

IDENTIFIER_TYPES = [
    IDENTIFIER_BATCH,
    IDENTIFIER_BARCODE,
    IDENTIFIER_QR,
]

# Medicine Units
UNITS = [
    "Tablets",
    "Capsules",
    "Strips",
    "Bottles",
    "Vials",
    "Ampoules",
    "ml",
    "mg",
    "Drops",
    "Sachets",
    "Puffs",
    "Ointment (g)",
]
