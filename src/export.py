# export.py — saves cleaned outputs for Power BI consumption
import pandas as pd
import logging
from pathlib import Path
from src.config import PROCESSED_DIR, CLEANED_FILENAME, SUMMARY_FILENAME

logger = logging.getLogger(__name__)

# ── Shared group columns — single source of truth ────────────────
SUMMARY_GROUP_COLS = [
    'platform', 'vehicle_class', 'time_period', 'time_period_order',
    'day_name', 'day_type', 'is_weekend', 'Distance(KM)'
]


def ensure_output_dir(output_dir: Path = PROCESSED_DIR) -> None:
    """Create the output directory if it doesn't exist."""
    output_dir.mkdir(parents=True, exist_ok=True)


def save_cleaned_rides(df: pd.DataFrame,
                       output_dir: Path = PROCESSED_DIR) -> Path:
    """Save the full cleaned long-format dataframe to CSV."""
    ensure_output_dir(output_dir)
    output_path = output_dir / CLEANED_FILENAME

    file_exists = output_path.exists()

    df.to_csv(
        output_path,
        mode   = 'a' if file_exists else 'w',
        header = not file_exists,
        index  = False
    )

    logger.info(f"{'Appended' if file_exists else 'Created'} {len(df)} rows → {output_path}")
    return output_path


def build_summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Build an aggregated summary table for Power BI."""
    summary = (
        df.groupby(SUMMARY_GROUP_COLS)
        .agg(
            price_mean    = ('price',         'mean'),
            price_median  = ('price',         'median'),
            price_min     = ('price',         'min'),
            price_max     = ('price',         'max'),
            ride_count    = ('price',         'count'),
            discount_count= ('is_discounted', 'sum'),
        )
        .round(2)
        .reset_index()
    )
    return summary


def update_summary_stats(new_summary: pd.DataFrame,
                         output_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """
    Merge new summary stats with existing ones using weighted mean.
    If no existing file, returns new_summary as-is.
    """
    output_path = output_dir / SUMMARY_FILENAME

    if not output_path.exists():
        return new_summary

    existing = pd.read_csv(output_path)

    # Merge old and new on group columns
    merged = pd.merge(
        existing, new_summary,
        on      = SUMMARY_GROUP_COLS,
        how     = 'outer',
        suffixes= ('_old', '_new')
    )

    # Fill missing counts with zero
    for col in ['ride_count', 'discount_count']:
        merged[f'{col}_old'] = merged[f'{col}_old'].fillna(0)
        merged[f'{col}_new'] = merged[f'{col}_new'].fillna(0)

    # Recalculate total counts
    merged['ride_count']     = merged['ride_count_old']     + merged['ride_count_new']
    merged['discount_count'] = merged['discount_count_old'] + merged['discount_count_new']

    # Weighted mean for price_mean
    merged['price_mean'] = (
        (merged['price_mean_old'].fillna(0) * merged['ride_count_old'] +
         merged['price_mean_new'].fillna(0) * merged['ride_count_new']) /
        merged['ride_count']
    ).round(2)

    # True min and max across old and new
    merged['price_min'] = merged[['price_min_old', 'price_min_new']].min(axis=1)
    merged['price_max'] = merged[['price_max_old', 'price_max_new']].max(axis=1)

    # Weighted approximation for median
    merged['price_median'] = (
        (merged['price_median_old'].fillna(0) * merged['ride_count_old'] +
         merged['price_median_new'].fillna(0) * merged['ride_count_new']) /
        merged['ride_count']
    ).round(2)

    # Keep only final columns
    final_cols = SUMMARY_GROUP_COLS + [
        'price_mean', 'price_median', 'price_min',
        'price_max', 'ride_count', 'discount_count'
    ]
    return merged[final_cols]


def save_summary_stats(df: pd.DataFrame,
                       output_dir: Path = PROCESSED_DIR) -> Path:
    """Build, merge, and save summary stats."""
    ensure_output_dir(output_dir)

    new_summary   = build_summary_stats(df)
    final_summary = update_summary_stats(new_summary, output_dir)

    output_path = output_dir / SUMMARY_FILENAME
    final_summary.to_csv(output_path, index=False)

    logger.info(f"Saved summary stats: {len(final_summary)} rows → {output_path}")
    return output_path


def run_export(df: pd.DataFrame,
               output_dir: Path = PROCESSED_DIR) -> dict:
    """Master export function — runs all saves and returns a report."""
    logger.info("Starting export...")

    cleaned_path = save_cleaned_rides(df, output_dir)
    summary_path = save_summary_stats(df, output_dir)

    return {
        'cleaned_path': cleaned_path,
        'summary_path': summary_path,
        'row_count':    len(df),
    }