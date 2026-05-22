import os
import json
import io
import boto3
from datetime import datetime, timedelta
import pandas as pd
import pyarrow as pa
import requests
from rapidfuzz import process, fuzz

# Connectiong to DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('VIN_Lookup')


def get_vin_metadata(vin_list):
    vin_map = {}
    # Only unique values
    for v in set(vin_list):
        res = table.get_item(Key={'vin': v})
        if 'Item' in res:
            vin_map[v] = (res['Item']['make'], res['Item']['model'])
    return vin_map


# Canonical names for standarize brand
canonical_mark = ["Ford", "Chevrolet", "Nissan", "Toyota", "Dodge", "Honda",
                  "Hyundai", "Bmw", "Kia", "Chrysler", "Mercedes-Benz", "Jeep",
                  "Infiniti", "Volkswagen", "Lexus", "Gmc", "Uknown", "Mazda",
                  "Cadillac", "Acura", "Audi", "Lincoln", "Buick", "Subaru",
                  "Ram", "Pontiac", "Mitsubishi", "Volvo", "Mini", "Saturn",
                  "Mercury", "Land Rover", "Scion", "Jaguar", "Porsche",
                  "Suzuki", "Fiat", "Hummer", "Saab", "Smart", "Oldsmobile",
                  "Isuzu", "Maserati", "Bentley", "Plymouth", "Aston Martin",
                  "Tesla", "Ferrari", "Geo", "Rolls-Royce", "Fisker",
                  "Lamborghini", "Daewoo", "Lotus", "Airstream"
                  ]
manual_mapping = {
    "Vw": "Volkswagen",
    "Chev Truck": "Chevrolet",
    "Dot": "Dodge"
}


def clean_make_fuzzy(input_make, canonical_list, threshold=80):
    if pd.isna(input_make) or input_make == 'Nan':
        return 'Unknown'

    if input_make in manual_mapping:
        return manual_mapping[input_make]

    match = process.extractOne(input_make, canonical_list, scorer=fuzz.WRatio, score_cutoff=threshold)

    if match:
        return match[0]
    return input_make


def lambda_handler(event, context):
    def process_enrichment(df):
        # Find rows to change
        mask = (df['make'] == 'Nan') | (df['make'].isna())
        vins_to_query = df.loc[mask, 'vin'].tolist()

        if not vins_to_query:
            return df

        # Get metadata for VINs
        lookup_data = get_vin_metadata(vins_to_query)

        # Create two maps for make and model
        make_map = {v: data[0] for v, data in lookup_data.items()}
        model_map = {v: data[1] for v, data in lookup_data.items()}

        # Update the dataframe
        # Only fill empty data to secure still existing old data
        df.loc[mask, 'make'] = df.loc[mask, 'vin'].map(make_map).fillna(df['make'])
        df.loc[mask, 'model'] = df.loc[mask, 'vin'].map(model_map).fillna(df['model'])

        return df

    # PARAMETERS
    BUCKET_NAME = os.environ.get('BUCKET_NAME')
    today = datetime.now()
    PARTITION_PREFIX = f'refined_data/year={today.year}/month={today.month}/'
    S3_KEY = f'{PARTITION_PREFIX}data_incremental.parquet'

    try:
        # 1. Load directly from S3 to Pandas
        s3 = boto3.client('s3')
        response = s3.get_object(Bucket=BUCKET_NAME, Key=event.get('raw_key'))
        df = pd.read_csv(io.BytesIO(response['Body'].read()))

        # 2. Cleaning data
        df = df.rename(columns={'year': 'release_year', 'trim': 'car_trim'})
        df.columns = [c.lower() for c in df.columns]
        # Not include records without VINs
        df = df[~((df['vin'].isna()) | (df['vin'] == 'Nan'))]
        # Enrich data from VINs information
        df = process_enrichment(df)
        # Brands names standardization
        df['make'] = df['make'].astype(str).str.title().str.strip()
        df['model'] = df['model'].astype(str).str.title().str.strip()
        # Entity Resolution (Fuzzy Matching) for brands
        unique_dirty_makes = df[~df['make'].isin(canonical_mark)]['make'].unique()
        corrections = {make: clean_make_fuzzy(make, canonical_mark) for make in unique_dirty_makes}
        df['make'] = df['make'].replace(corrections)

        # 3. Delete old month and upload new as Parquet
        # Calculate the previous month
        first_day_of_current_month = today.replace(day=1)
        last_month_date = first_day_of_current_month - timedelta(days=1)

        prev_year = last_month_date.year
        prev_month = last_month_date.month

        # Define the prefix to delete
        old_prefix = f"refined_data/year={prev_year}/month={prev_month}/"
        s3_res = boto3.resource('s3')
        bucket = s3_res.Bucket(BUCKET_NAME)

        # Delete old objects in that prefix
        print(f"Cleaning up old data from: {old_prefix}")
        bucket.objects.filter(Prefix=old_prefix).delete()

        # Upload parquet to S3
        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, index=False)

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=S3_KEY,
            Body=parquet_buffer.getvalue()
        )

        return {
            "statusCode": 200,
            "year": today.year,
            "month": today.month,
            "partition_location": f"s3://{BUCKET_NAME}/{PARTITION_PREFIX}"
        }

    except Exception as e:
        raise e  # Important: throwing error to be catched by SNS