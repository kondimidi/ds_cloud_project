import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import TransformedTargetRegressor
from sklearn import clone
from xgboost import XGBRegressor
from category_encoders import TargetEncoder

# --- CONFIGURATION ---
LUXURY_BRANDS = ['Rolls-Royce','Ferrari','Lamborghini','Airstream','Tesla','Bentley','Aston Martin','Maserati', 'Porsche', 'Land Rover']
FEATURES = ['make', 'car_age', 'condition', 'odometer', 'year_condition','model_clean', 'body_clean', 'state', 'is_luxury']

def preprocess_data(df):
    df = df.copy()
    df['car_age'] = 2026 - df['year']
    df['year_condition'] = df['year'] * df['condition']

    # Cleaning categories
    df['state'] = df['state'].astype(str)
    df = df[df['state'].str.len() <= 2]

    df['body_clean'] = df['body'].astype(str).str.title().str.strip()
    df['model_clean'] = df['model'].astype(str).str.title().str.strip()

    # Filtering records (for training purpose only - in production everything will be priced)
    df = df[(~df['sellingprice'].isna()) & (df['sellingprice'] > 1)]
    df = df[df['make'] != 'Unknown']
    df['is_luxury'] = df['make'].isin(LUXURY_BRANDS).astype(int)

    return df

# --- MAIN PROCESS ---
if __name__ == "__main__":
    # 1. Loading data
    base_path = Path(__file__).resolve().parent.parent.parent
    df_raw = pd.read_csv(base_path / "data" / "car_prices.csv")
    df = preprocess_data(df_raw)

    # 2. Definition of the base Pipeline
    base_pipeline = Pipeline(steps=[
        ('encoder', TargetEncoder(cols=['make', 'model_clean', 'body_clean', 'state'])),
        ('regressor', XGBRegressor(n_estimators=1000, learning_rate=0.05, random_state=42, n_jobs=-1))
    ])

    log_model_template = TransformedTargetRegressor(
        regressor=base_pipeline,
        func=np.log1p,
        inverse_func=np.expm1
    )

    # 3. Division and training luxury brands
    df_luxury = df[df['is_luxury'] == 1]
    model_luxury = clone(log_model_template).set_params(regressor__regressor__max_depth=5)
    model_luxury.fit(df_luxury[FEATURES], df_luxury['sellingprice'])


    # 4. Division and training normal brands
    df_normal = df[df['is_luxury'] == 0]
    model_normal = clone(log_model_template).set_params(regressor__regressor__max_depth=9)
    model_normal.fit(df_normal[FEATURES], df_normal['sellingprice'])

    # 5. Export for production
    joblib.dump(model_luxury, base_path / "models" / "model_luxury.joblib")
    joblib.dump(model_normal, base_path / "models" / "model_normal.joblib")