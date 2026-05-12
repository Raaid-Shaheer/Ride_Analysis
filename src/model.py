# model.py — train, evaluate and export price prediction models
import pandas as pd
import numpy as np
import pickle
import logging
from pathlib import Path
from sklearn.linear_model    import LinearRegression
from sklearn.ensemble        import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing   import OneHotEncoder
from sklearn.compose         import ColumnTransformer
from sklearn.pipeline        import Pipeline
from sklearn.metrics         import mean_squared_error, mean_absolute_error, r2_score
from src.config import PROCESSED_DIR, VEHICLE_MAP
from src.cleaner import get_time_period
logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────
MODELS_DIR = PROCESSED_DIR.parent / "models"

# ── Feature definitions ──────────────────────────────────────────
NUMERIC_FEATURES     = ['Distance(KM)', 'hour', 'day_of_week']
CATEGORICAL_FEATURES = ['vehicle_class', 'time_period']
TARGET               = 'price'

# ── Models to compare ────────────────────────────────────────────
def get_candidate_models() -> dict:
    """
    Return fresh model instances every call.
    Never reuse fitted model objects across pipelines.
    """
    return {
        'LinearRegression': LinearRegression(),
        'RandomForest':     RandomForestRegressor(n_estimators=100, random_state=42),
        'GradientBoosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
    }


def load_training_data(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    df = pd.read_csv(processed_dir / "cleaned_rides.csv")
    df = df.dropna(subset=["price"])
    df = df[~df['vehicle_class'].isin(['Parcel_Tuk', 'Parcel_Bike'])]
    logger.info(f"Training data loaded: {len(df):,} rows")
    return df


def build_preprocessor() -> ColumnTransformer:

    return ColumnTransformer(transformers=[
        ('num', 'passthrough', NUMERIC_FEATURES),
        ('cat', OneHotEncoder(handle_unknown='ignore'), CATEGORICAL_FEATURES),
    ])


def evaluate_model(model, X_test: pd.DataFrame,
                   y_test: pd.Series, model_name: str) -> dict:

    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae  = mean_absolute_error(y_test, y_pred)
    r2   = r2_score(y_test, y_pred)

    logger.info(f"{model_name:20s} | RMSE: {rmse:8.2f} | MAE: {mae:8.2f} | R²: {r2:.4f}")

    return {
        'model_name': model_name,
        'rmse':       rmse,
        'mae':        mae,
        'r2':         r2,
    }


def train_platform_model(df: pd.DataFrame,
                         platform: str) -> tuple[Pipeline, dict]:

    platform_df = df[df['platform'] == platform].copy()
    logger.info(f"Training {platform} model on {len(platform_df):,} rows")

    X = platform_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = platform_df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size    = 0.2,
        random_state = 42
    )


    results      = []
    pipelines    = {}

    for model_name, model in get_candidate_models().items():
        preprocessor = build_preprocessor()
        pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('model',        model)
        ])

        pipeline.fit(X_train,y_train )
        metrics = evaluate_model(pipeline, X_test, y_test, model_name)
        results.append(metrics)
        pipelines[model_name] = pipeline

    # Select best by lowest RMSE
    results_df   = pd.DataFrame(results)
    best_row     = results_df.loc[results_df['rmse'].idxmin()]
    best_name    = best_row['model_name']
    best_pipeline = pipelines[best_name]

    logger.info(f"Best model for {platform}: {best_name} "
                f"(RMSE: {best_row['rmse']:.2f}, R²: {best_row['r2']:.4f})")

    return best_pipeline, best_row.to_dict()


def save_model(pipeline: Pipeline, platform: str) -> Path:

    MODELS_DIR.mkdir( parents=True, exist_ok=True )
    model_path = MODELS_DIR / f"model_{platform.lower()}.pkl"

    with open(model_path, 'wb') as f:
        pickle.dump(pipeline, f)

    logger.info(f"Saved {platform} model → {model_path}")
    return model_path


def generate_predictions_grid(pipeline: Pipeline,
                               platform: str,df:  pd.DataFrame) -> pd.DataFrame:
    # Get actual vehicle classes from the trained model's training data
    vehicle_classes = df[df['platform'] == platform]['vehicle_class'].unique()

    # Build all combinations
    rows = []
    for distance in range(1, 21):
        for hour in range(0, 24):
            for dow in range(0, 7):
                for vehicle in vehicle_classes:
                    rows.append({
                        'Distance(KM)':  distance,
                        'hour':          hour,
                        'day_of_week':   dow,
                        'vehicle_class': vehicle,
                        'time_period':   get_time_period(hour),
                        'is_weekend':    dow >= 5,
                    })

    grid_df = pd.DataFrame(rows)

    X_grid           = grid_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    grid_df['price'] = pipeline.predict(X_grid)
    grid_df['price'] = grid_df['price'].round(2).clip(lower=0)
    grid_df['platform'] = platform

    return grid_df


def run_model_pipeline(processed_dir: Path = PROCESSED_DIR) -> dict:
    """
    Master function — trains both platform models, saves them,
    generates prediction grids, exports predictions.csv for Power BI.

    """
    df = load_training_data(processed_dir)

    # Train both platforms
    pickme_pipeline, pickme_metrics = train_platform_model(df, 'PickMe')
    uber_pipeline,   uber_metrics   = train_platform_model(df, 'Uber')


    # Save models
    save_model(pickme_pipeline, 'PickMe')
    save_model(uber_pipeline,   'Uber')

    # Generate prediction grids
    pickme_grid = generate_predictions_grid(pickme_pipeline, 'PickMe',df)
    uber_grid   = generate_predictions_grid(uber_pipeline,   'Uber',df)

    # Combine and save
    predictions = pd.concat([pickme_grid, uber_grid], ignore_index=True)
    output_path = processed_dir / "predictions.csv"
    predictions.to_csv(output_path, index=False)
    logger.info(f"Saved predictions grid: {len(predictions):,} rows → {output_path}")

    return {
        'pickme': pickme_metrics,
        'uber':   uber_metrics,
        'predictions_path': output_path,
        'prediction_rows':  len(predictions),
    }