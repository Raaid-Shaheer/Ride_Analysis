
import pandas as pd
import logging
from pathlib import Path
from src.config import RAW_DIR, PROCESSED_DIR, EXCLUDED_ROUTES, COLUMN_ALIASES


logger = logging.getLogger(__name__)

PROCESSED_LOG = PROCESSED_DIR / ".processed_log"


def get_processed_files() -> set:
    if not PROCESSED_LOG.exists():
        return set()
    return set(PROCESSED_LOG.read_text().splitlines())


def mark_files_as_processed(filepaths: list[Path]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_LOG, 'a') as f:
        for filepath in filepaths:
            f.write(filepath.name + '\n')

def parse_capture_time(time_str: str) -> str:
    """
    Normalise capture time from filename to 24hr HH:MM:SS string.
    Handles both '14-00-00' (old 24hr) and '12-52-28 PM' (new 12hr).
    Always outputs 24hr so the rest of the pipeline needs zero changes.

    Examples:
        '14-00-00'    → '14:00:00'
        '12-52-28 PM' → '12:52:28'
        '06-00-00 AM' → '06:00:00'
    """
    time_str = time_str.strip()
    try:
        if 'AM' in time_str.upper() or 'PM' in time_str.upper():
            # 12hr format — replace dashes with colons then parse
            t = pd.to_datetime(
                time_str.replace('-', ':'),
                format='%I:%M:%S %p'
            )
        else:
            # 24hr format
            t = pd.to_datetime(
                time_str.replace('-', ':'),
                format='%H:%M:%S'
            )
        return t.strftime('%H:%M:%S')   # always output 24hr

    except Exception:
        logger.warning(f"Could not parse capture time: '{time_str}' — defaulting to 00:00:00")
        return "00:00:00"

def extract_metadata_from_filename(filepath: Path) -> dict:
    """
    Extract route group, date and capture time from filename.

    Examples:
        OutputUber_A_To_B_2026-04-27_14-00-00.csv
        OutputUber_Gampaha_2026-05-04_12-52-28 PM.csv
    """
    stem  = filepath.stem.strip()   # strip trailing spaces
    parts = stem.split("_")

    route_group  = "_".join(parts[1:-2])          # everything between prefix and date
    capture_date = parts[-2]                       # second to last = date
    capture_time = parse_capture_time(parts[-1])   # last = time, normalised to 24hr

    return {
        "route_group":  route_group,
        "capture_date": capture_date,
        "capture_time": capture_time,
    }

def validate_schema(df: pd.DataFrame, filepath: Path) -> bool:
    REQUIRED_COLUMNS = [
        "Distance(KM)", "Date", "Time",
        "Pickup Location", "Drop Location",
    ]
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        logger.warning(f"Schema mismatch in {filepath.name}: missing {missing}")
        return False
    return True


def load_single_file(filepath: Path) -> pd.DataFrame | None:
    try:
        df = pd.read_csv(filepath)
        if not validate_schema(df, filepath):
            return None

        df = df.dropna(axis=1, how="all")
        df.columns = df.columns.str.strip()
        df = df.rename(columns=COLUMN_ALIASES)
        meta = extract_metadata_from_filename(filepath)
        for key, value in meta.items():
            df[key] = value
        logger.info(f"Loaded {filepath.name}: {len(df)} rows, {len(df.columns)} cols")
        return df
    except Exception as e:
        logger.error(f"Failed to load {filepath.name}: {e}")
        return None


def load_all_files(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Incremental loader — only processes files not already in the log."""
    all_files       = sorted(raw_dir.glob("*.csv"))
    processed_names = get_processed_files()
    new_files       = [f for f in all_files if f.name not in processed_names]

    if not new_files:
        logger.info("No new files to process — pipeline is up to date")
        return pd.DataFrame()

    logger.info(f"Found {len(new_files)} new files to process")

    dataframes   = []
    loaded_files = []

    for filepath in new_files:
        df = load_single_file(filepath)
        if df is not None:
            dataframes.append(df)
            loaded_files.append(filepath)

    if not dataframes:
        raise FileNotFoundError(f"No valid new CSV files found in {raw_dir}")

    mark_files_as_processed(loaded_files)

    master = pd.concat(dataframes, ignore_index=True)

    # Filter out test routes
    master = master[~master['route_group'].isin(EXCLUDED_ROUTES)]

    logger.info(f"Master dataframe: {len(master)} rows from {len(dataframes)} new files")
    return master