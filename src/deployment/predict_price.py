import json
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
        # 1. Handle API Gateway proxy integration wrapper vs direct AWS console test
        if 'body' in event:
            body_data = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            car_info = body_data['car_data']
        else:
            car_info = event['car_data']

        df_raw = pd.DataFrame([car_info])
        
        # 2. Data clean
        df_clean = preprocess_data(df_raw, is_training=False)

        # Defensive check against empty dataframes
        if df_clean.empty:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Data preprocessing failed. Input row was dropped."})
            }
        
        # 3. Features
        features = ['make', 'car_age', 'condition', 'odometer', 'year_condition',
                    'model_clean', 'body_clean', 'state', 'is_luxury']
        
        # 4. Pricing logic
        if df_clean['is_luxury'].iloc[0] == 1:
            price = model_lux.predict(df_clean[features])[0] * 1.15
        else:
            price = model_norm.predict(df_clean[features])[0]
            
        # 5. Safe Response formatting for API Gateway Proxy
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"predicted_price": round(float(price), 2)})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": str(e)})
        }