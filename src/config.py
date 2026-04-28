# config.py — all settings in one place, never hardcode paths elsewhere
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).resolve().parent.parent
RAW_DIR       = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# ── Vehicle equivalency map ──────────────────────────────────────

VEHICLE_MAP = {
    "Bike": {
        "pickme": "pickmeBike",
        "uber":   "uberMoto",
    },
    "Tuk": {
        "pickme": "pickmeTuk",
        "uber":   "uberTuk",
    },
    "Economy": {
        "pickme": "pickmeFlex",
        "uber":   "uberZip",
    },
    "Standard": {
        "pickme": "pickmeMini",
        "uber":   "uberZip_Plus",
    },
    "Premium": {
        "pickme": "pickmeCar",
        "uber":   "uberPremier",
    },
    "Parcel_Bike": {
        "pickme": "pickmeFlash",
        "uber":   "uberParcel_Bike",
    },
    "Parcel_Tuk": {
        "pickme": "pickmeFlashL",
        "uber":   "uberParcel_Tuk",
    },
}

# ── Platform display names ───────────────────────────────────────
PLATFORM_NAMES = {
    "pickme": "PickMe",
    "uber":   "Uber",
}

# ── Time period bins (hour → label) ─────────────────────────────
TIME_PERIODS = {
    "Late Night":    range(0,  5),   # 00:00–04:59
    "Early Morning": range(5,  7),   # 05:00–06:59
    "Morning Rush":  range(7, 10),   # 07:00–09:59  ← peak
    "Midday":        range(10, 16),  # 10:00–15:59
    "Evening Rush":  range(16, 20),  # 16:00–19:59  ← peak
    "Night":         range(20, 24),  # 20:00–23:59
}

# ── Data quality thresholds ──────────────────────────────────────
MIN_PRICE    = 50      # LKR — below this is suspect
MAX_PRICE    = 15000   # LKR — above this is suspect
MIN_DISTANCE = 1       # km
MAX_DISTANCE = 100     # km

# ── Output filenames ─────────────────────────────────────────────
CLEANED_FILENAME     = "cleaned_rides.csv"
PREDICTIONS_FILENAME = "predictions.csv"
SUMMARY_FILENAME     = "summary_stats.csv"