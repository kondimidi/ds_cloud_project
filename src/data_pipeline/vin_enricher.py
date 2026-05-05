import boto3
import pandas as pd
import requests
import io
import os
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('VIN_Lookup')

def decode_vins_batch(vin_list):
    url = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/"
    vin_string = ";".join(vin_list)
    payload = {'format': 'json', 'data': vin_string}
    try:
        response = requests.post(url, data=payload, timeout=25)
        if response.status_code == 200:
            return response.json().get('Results', [])
    except Exception as e:
        print(f"API Error: {e}")
    return []

def lambda_handler(event, context):
    # 1. Directory
    BUCKET_NAME = os.environ.get('BUCKET_NAME')

    current_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    S3_KEY = f"raw_data/{current_date}/car_prices.csv"

    try:
        # 2. Upload csv from S3
        response = s3.get_object(Bucket=BUCKET_NAME, Key=S3_KEY)
        df = pd.read_csv(io.BytesIO(response['Body'].read()))

        # 3. Choosing VIN
        missing_mask = (df['make'] == 'Nan') | (df['make'].isna())
        vins_to_check = df[missing_mask]['vin'].unique().tolist()

        if not vins_to_check:
            return {"status": "No missing makes found"}

        # 4. Filtering by DynamoDB
        vins_to_decode = []
        for v in vins_to_check:
            if len(vins_to_decode) >= 1000: break

            res = table.get_item(Key={'vin': v}, ProjectionExpression='vin')
            if 'Item' not in res:
                vins_to_decode.append(v)

        if not vins_to_decode:
            return {"status": "All VINs already in DynamoDB"}

        # 5. Downloading data by API and saving im DynamoDB
        all_decoded = []
        for i in range(0, len(vins_to_decode), 10):
            batch = vins_to_decode[i:i + 10]
            results = decode_vins_batch(batch)
            all_decoded.extend(results)

        with table.batch_writer() as batch_writer:
            for item in all_decoded:
                if item.get('Make'):
                    batch_writer.put_item(
                        Item={
                            'vin': item['VIN'],
                            'make': item['Make'],
                            'model': item['Model']
                        }
                    )
        return {
            "status": "Success",
            "vins_added_to_db": len(all_decoded),
            "source_file": S3_KEY
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        # Sending manually note to SNS
        sns = boto3.client('sns')
        sns.publish(
            TopicArn=os.environ.get('SNS_TOPIC_ARN'),
            Message=f"Lambda failed: {str(e)}",
            Subject="PIPELINE ERROR ALERT"
        )
        raise e  # Important: throwing error to be catched by SNS