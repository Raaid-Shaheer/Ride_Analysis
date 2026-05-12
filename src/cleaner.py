# cleaner.py — all cleaning logic, one function per concern

from typing import Any

import pandas as pd
import logging
from src.config import (MIN_PRICE, MAX_PRICE, MIN_DISTANCE, MAX_DISTANCE,
                    VEHICLE_MAP, TIME_PERIODS, PLATFORM_NAMES, TIME_PERIOD_ORDER)
from numpy import dtype, integer, ndarray

logger = logging.getLogger(__name__)

def fix_price_column(series: pd.Series) -> pd.Series:
    series = pd.Series(series)   #  normalise input
    return pd.to_numeric(
        series.astype(str).str.replace(',', '').str.strip(),
        errors='coerce'
    )


def get_time_period(hour: int) -> str:
    """Map an hour integer to a named time period."""
    for period, hour_range in TIME_PERIODS.items():
        if hour in hour_range:
            return period
    return "Unknown"


def parse_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """Build datetime features from date + capture_time."""
    df['datetime'] = pd.to_datetime(
        df['capture_date'] + ' ' + df['capture_time'],
        format='%Y-%m-%d %H:%M:%S'
    )
    df['hour']        = df['datetime'].dt.hour
    df['day_of_week'] = df['datetime'].dt.dayofweek
    df['day_name']    = df['datetime'].dt.day_name()
    df['is_weekend']  = df['day_of_week'].isin([5, 6])
    df['time_period'] = df['hour'].apply(get_time_period)
    df['day_type'] = df['is_weekend'].map({True: 'Weekend', False: 'Weekday'})

    df.drop(columns=['Date', 'Time', 'capture_date', 'capture_time'],  # ← typo fixed
            inplace=True)

    # Sort order for time periods — used by Power BI for correct ordering
    df['time_period_order'] = df['time_period'].map(TIME_PERIOD_ORDER)

    return df


def flag_and_clean_discounts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean price columns and extract discount flags and amounts.

    Schema (both platforms, new unified definition):
        Price = original price
        Dis   = discounted price, or 0 if no discount

    If Dis > 0  → customer pays Dis, saving = Price - Dis
    If Dis = 0  → customer pays Price, no discount

    After this function, Price column always contains what
    the customer actually pays — downstream never needs to
    think about discounts again.
    """
    dis_cols = [c for c in df.columns
                if c.endswith('Dis') and c != 'Distance(KM)']

    for dis_col in dis_cols:
        price_col = dis_col.replace('Dis', 'Price')

        if price_col not in df.columns:
            continue

        df[dis_col]   = fix_price_column(df[dis_col])
        df[price_col] = fix_price_column(df[price_col])

        flag_col    = price_col.replace('Price', '_is_discounted')
        savings_col = price_col.replace('Price', '_discount_amt')

        # Discount exists when Dis > 0
        has_discount = df[dis_col] > 0

        df[flag_col]    = has_discount

        # Saving = original - discounted, zero where no discount
        df[savings_col] = (
            (df[price_col] - df[dis_col])
            .where(has_discount, 0)
            .clip(lower=0)
            .fillna(0)
        )

        # Overwrite price with what customer actually pays
        df[price_col] = df[price_col].where(~has_discount, df[dis_col])

        df.drop(columns=[dis_col], inplace=True)

    # Surge columns are text flags only — drop them
    surge_cols = [c for c in df.columns if 'Surge' in c or 'surge' in c]
    df.drop(columns=surge_cols, inplace=True)

    return df



def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Clip extreme prices and remove invalid distances."""
    price_cols = [c for c in df.columns if 'Price' in c or 'price' in c]

    for col in price_cols:
        before_nulls = df[col].isna().sum()
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].clip(lower=MIN_PRICE, upper=MAX_PRICE)
        logger.info(f"Clipped {col} — nulls before: {before_nulls}")

    invalid_dist = df[
        (df['Distance(KM)'] < MIN_DISTANCE) |
        (df['Distance(KM)'] > MAX_DISTANCE)
    ]
    if len(invalid_dist) > 0:
        logger.warning(f"Removed {len(invalid_dist)} rows with invalid distances")
        df = df[
            (df['Distance(KM)'] >= MIN_DISTANCE) &
            (df['Distance(KM)'] <= MAX_DISTANCE)
        ]
    return df


def reshape_to_long(df: pd.DataFrame) -> pd.DataFrame:
    """Reshape wide format to long format for Power BI."""
    base_cols = [
        'Distance(KM)', 'Pickup Location', 'Drop Location',
        'datetime', 'hour', 'day_of_week', 'day_name',
        'is_weekend','day_type','time_period','time_period_order', 'route_group'
    ]
    base_cols = [c for c in base_cols if c in df.columns]  # defensive filter
    long_frames = []

    for vehicle_class, platforms in VEHICLE_MAP.items():
        for platform, col_prefix in platforms.items():
            price_col      = f"{col_prefix}Price"
            discounted_col = f"{col_prefix}_is_discounted"
            savings_col    = f"{col_prefix}_discount_amt"

            if price_col not in df.columns:
                continue

            temp = df[base_cols].copy()
            temp['platform']      = PLATFORM_NAMES[platform]
            temp['vehicle_class'] = vehicle_class
            temp['price']         = df[price_col]
            temp['is_discounted'] = df.get(discounted_col, False)
            temp['discount_amt']  = df.get(savings_col, 0)

            long_frames.append(temp)

    if not long_frames:
        raise ValueError("No vehicle columns matched VEHICLE_MAP — check config")

    long_df = pd.concat(long_frames, ignore_index=True)
    long_df  = long_df.dropna(subset=['price'])

    logger.info(f"Reshaped to long format: {len(long_df)} rows")
    return long_df


def run_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """Master cleaning pipeline — runs every step in correct order."""
    logger.info("Starting cleaning pipeline...")
    df = parse_datetime(df)
    df = flag_and_clean_discounts(df)
    df = remove_outliers(df)
    df = reshape_to_long(df)
    logger.info(f"Pipeline complete. Final shape: {df.shape}")
    return df