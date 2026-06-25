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
from datetime  import datetime

# --- CONFIGURATION ---
LUXURY_BRANDS = ['Rolls-Royce','Ferrari','Lamborghini','Airstream','Tesla','Bentley','Aston Martin','Maserati', 'Porsche', 'Land Rover']
FEATURES = ['make', 'car_age', 'condition', 'odometer', 'year_condition','model_clean', 'body_clean', 'state', 'is_luxury', 'inflation_multiplier']

def inject_inflation_feature(df, cpi_series):
    df['cpi_sale'] = df['sale_year'].map(cpi_series).fillna(1.0)
    df['cpi_prod'] = df['year'].map(cpi_series).fillna(1.0)

    df['inflation_multiplier'] = df['cpi_sale'] / df['cpi_prod']

    df['inflation_multiplier'] = np.where(df['sale_year'] <= df['year'], 1.0, df['inflation_multiplier'])

    df= df.drop(columns=['cpi_sale', 'cpi_prod'])
    
    return df

def preprocess_data(df, is_training=False):
    inflation_history = {
        1982: 3.80, 1983: 3.80, 1984: 3.90, 1985: 3.80, 1986: 1.10,
        1987: 4.40, 1988: 4.40, 1989: 4.60, 1990: 6.10, 1991: 3.10,
        1992: 2.90, 1993: 2.70, 1994: 2.70, 1995: 2.50, 1996: 3.30,
        1997: 1.70, 1998: 1.60, 1999: 2.70, 2000: 3.40, 2001: 1.60,
        2002: 2.40, 2003: 1.90, 2004: 3.30, 2005: 3.40, 2006: 2.50,
        2007: 4.10, 2008: 0.10, 2009: 2.70, 2010: 1.50, 2011: 3.00,
        2012: 1.70, 2013: 1.50, 2014: 0.80, 2015: 0.70, 2016: 2.10,
        2017: 2.10, 2018: 1.90, 2019: 2.30, 2020: 1.40, 2021: 7.00,
        2022: 6.50, 2023: 3.40, 2024: 2.90, 2025: 2.68, 2026: 2.77
    }

    rates = pd.Series(inflation_history) / 100 + 1
    cpi_timeline = rates.cumprod()
    cpi_timeline[1981] = 1.0
    cpi_timeline = cpi_timeline.sort_index()

    df = df.copy()
    current_year = datetime.now().year

    if is_training:
        df['saledate'] = pd.to_datetime(df['saledate'], errors='coerce', utc=True, format='mixed')
        df['sale_year'] = np.where(df['saledate'].isna(), df['year'], df['saledate'].dt.year).astype(int)
        df['car_age'] = df['sale_year'] - df['year']
        
        df = df[df['state'].str.len() <= 2]
        df = df[(~df['sellingprice'].isna()) & (df['sellingprice'] > 1)]
        df = df[df['make'] != 'Unknown']
    else:
        df['sale_year'] = current_year
        df['car_age'] = current_year - df['year']

    df['year_condition'] = df['year'] * df['condition']
    df['state'] = df['state'].astype(str)
    df['body_clean'] = df['body'].astype(str).str.title().str.strip()
    df['model_clean'] = df['model'].astype(str).str.title().str.strip()
    df['is_luxury'] = df['make'].isin(LUXURY_BRANDS).astype(int)

    df = inject_inflation_feature(df, cpi_timeline)

    return df

# --- MAIN PROCESS ---
if __name__ == "__main__":
    # 1. Loading data
    base_path = Path(__file__).resolve().parent.parent.parent
    df_raw = pd.read_csv(base_path / "data" / "car_prices.csv")

    # Set is_training=True to drop bad records for training
    df = preprocess_data(df_raw, is_training=True)

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
    joblib.dump(model_luxury, base_path / "models" / "latest" / "model_luxury.joblib")
    joblib.dump(model_normal, base_path / "models" / "latest" / "model_normal.joblib")