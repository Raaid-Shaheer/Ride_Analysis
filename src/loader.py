# loader.py — safely load and combine all CSVs into one master dataframe
import pandas as pd
import logging
from pathlib import Path
from config import RAW_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_metadata_from_filename(filepath: Path) -> dict:
    """
    OutputUber_A_To_B_2026-04-27_00-00-00.csv
    splits into:
    ['OutputUber', 'A', 'To', 'B', '2026-04-27', '00-00-00']
         [0]       [1]  [2]  [3]       [4]            [5]
    """
    stem  = filepath.stem
    parts = stem.split("_")

    route_group  = f"{parts[1]}_To_{parts[3]}"   # "A_To_B"
    capture_date = parts[4]                        # "2026-04-27"
    capture_time = parts[5].replace("-", ":")      # "00:00:00"

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