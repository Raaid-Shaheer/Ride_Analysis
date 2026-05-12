import pandas as pd
from src.config import PROCESSED_DIR, VEHICLE_MAP
from src.cleaner import get_time_period

df = pd.read_csv(PROCESSED_DIR / "cleaned_rides.csv")
df = df[~df['vehicle_class'].isin(['Parcel_Tuk', 'Parcel_Bike'])]

# Simulate exactly what generate_predictions_grid does
vehicle_classes = df[df['platform'] == 'PickMe']['vehicle_class'].unique()

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

NUMERIC_FEATURES     = ['Distance(KM)', 'hour', 'day_of_week']
CATEGORICAL_FEATURES = ['vehicle_class', 'time_period']

X_grid = grid_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]

print("Grid vehicle_class unique:", sorted(X_grid['vehicle_class'].unique()))
print("Grid time_period unique:",   sorted(X_grid['time_period'].unique()))
print("Grid shape:", X_grid.shape)

# Now load model and check what happens when preprocessor transforms
import pickle
with open(PROCESSED_DIR.parent / "models" / "model_pickme.pkl", "rb") as f:
    pipeline = pickle.load(f)

preprocessor = pipeline.named_steps['preprocessor']
transformed  = preprocessor.transform(X_grid)
print("Transformed shape:", transformed.shape)