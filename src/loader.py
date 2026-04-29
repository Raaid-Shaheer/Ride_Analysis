# loader.py — safely load and combine all CSVs into one master dataframe
import pandas as pd
import logging
from pathlib import Path
from src.config import RAW_DIR,PROCESSED_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROCESSED_LOG = PROCESSED_DIR / ".processed_log"


def get_processed_files() -> set:
    """
    Read the log of already-processed filenames.
    Returns a set of filenames (not full paths) that are already done.
    """
    if not PROCESSED_LOG.exists():
        return set()

    return set(PROCESSED_LOG.read_text().splitlines())


def mark_files_as_processed(filepaths: list[Path]) -> None:
    """
    Append newly processed filenames to the log.
    Uses append mode so we never overwrite the history.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    with open(PROCESSED_LOG, 'a') as f:
        for filepath in filepaths:
            f.write(filepath.name + '\n')


def load_all_files(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """
    Load only NEW unprocessed CSVs from raw_dir.
    Skips any file already recorded in the processed log.
    """
    all_files = sorted(raw_dir.glob("*.csv"))
    processed_names = get_processed_files()

    # Filter to only new files
    new_files = [f for f in all_files if f.name not in processed_names]

    if not new_files:
        logger.info("No new files to process — pipeline is up to date")
        return pd.DataFrame()  # empty dataframe

    logger.info(f"Found {len(new_files)} new files to process")

    dataframes = []
    loaded_files = []

    for filepath in new_files:
        df = load_single_file(filepath)
        if df is not None:
            dataframes.append(df)
            loaded_files.append(filepath)  # track only successfully loaded ones

    if not dataframes:
        raise FileNotFoundError(f"No valid new CSV files found in {raw_dir}")

    # Mark as processed ONLY after successful load
    mark_files_as_processed(loaded_files)

    master = pd.concat(dataframes, ignore_index=True)
    logger.info(f"Master dataframe: {len(master)} rows from {len(dataframes)} new files")
    return master

def extract_metadata_from_filename(filepath: Path) -> dict:
    stem  = filepath.stem
    parts = stem.split("_")

    route_group = "_".join(parts[1:-2])
    capture_date = parts[-2]
    capture_time = parts[-1].replace("-", ":")

    return {
        "route_group":  route_group,
        "capture_date": capture_date,
        "capture_time": capture_time,
    }


def validate_schema(df: pd.DataFrame, filepath: Path) -> bool:
    """
    Only enforce the structural minimum — vehicle columns are optional.
    """
    REQUIRED_COLUMNS = [
        "Distance(KM)",
        "Date",
        "Time",
        "Pickup Location",
        "Drop Location",
    ]

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        logger.warning(f"Schema mismatch in {filepath.name}: missing {missing}")
        return False
    return True


def load_single_file(filepath: Path) -> pd.DataFrame | None:
    """
    Load one CSV safely with full error handling.
    Returns None if file is unreadable — never crashes the whole pipeline.
    """
    try:
        df = pd.read_csv(filepath)

        if not validate_schema(df, filepath):
            return None


        df = df.dropna(axis=1, how="all")

        # Attach metadata from filename
        meta = extract_metadata_from_filename(filepath)
        for key, value in meta.items():
            df[key] = value

        logger.info(f"Loaded {filepath.name}: {len(df)} rows, {len(df.columns)} cols")
        return df

    except Exception as e:
        logger.error(f"Failed to load {filepath.name}: {e}")
        return None


def load_all_files(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """
    Load and combine every CSV in the raw directory into one master dataframe.
    """
    csv_files = sorted(raw_dir.glob("*.csv"))   # ← Path.glob, not glob.glob

    dataframes = []
    for filepath in csv_files:
        df = load_single_file(filepath)
        if df is not None:
            dataframes.append(df)

    if not dataframes:
        raise FileNotFoundError(f"No valid CSV files found in {raw_dir}")

    master = pd.concat(dataframes, ignore_index=True)
    logger.info(f"Master dataframe: {len(master)} rows from {len(dataframes)} files")
    return master