import joblib
import pandas as pd
from pathlib import Path
from train_models import preprocess_data

# Paths in Docker
BASE_PATH = Path("/var/task") 
model_lux = joblib.load(BASE_PATH / "models" / "model_luxury.joblib")
model_norm = joblib.load(BASE_PATH / "models" / "model_normal.joblib")

def lambda_handler(event, context):
    try:
        # 1. The lambda function receives data in an 'event'
        # Receive JSON: {"car_data": {"make": "Ford", "year": 2014, ...}}
        car_info = event['car_data']
        df_raw = pd.DataFrame([car_info])
        
        # 2. Data clean
        df_clean = preprocess_data(df_raw)
        
        # 3. Features
        features = ['make', 'car_age', 'condition', 'odometer', 'year_condition',
                    'model_clean', 'body_clean', 'state', 'is_luxury']
        
        # 4. Pricing logic
        if df_clean['is_luxury'].iloc[0] == 1:
            price = model_lux.predict(df_clean[features])[0] * 1.15
        else:
            price = model_norm.predict(df_clean[features])[0]
            
        return {
            "statusCode": 200,
            "body": {"predicted_price": round(float(price), 2)}
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": {"error": str(e)}
        }