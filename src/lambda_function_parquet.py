import os
import json
import boto3
from datetime import datetime
import awswrangler as wr
import pandas as pd


def lambda_handler(event, context):
    # PARAMETERS
    BUCKET_NAME = os.environ.get('BUCKET_NAME')
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Where we read from (file uploaded by the first Lambda)
    S3_SOURCE_PATH = f's3://{BUCKET_NAME}/raw_data/{current_date}/car_prices.csv'

    # Where do we store Parquet
    S3_DEST_PATH = f's3://{BUCKET_NAME}/refined_data/year={datetime.now().year}/month={datetime.now().month}/'

    try:
        # 1. Load directly from S3 to Pandas
        print(f"Reading CSV from S3: {S3_SOURCE_PATH}")

        # Wrangler taking care of communication with S3
        df = wr.s3.read_csv(path=S3_SOURCE_PATH)

        # 2. Cleaning columns names
        df = df.rename(columns={'year': 'release_year', 'trim': 'car_trim'})
        df.columns = [c.lower() for c in df.columns]

        # 3. Upload as Parquet
        print(f"Uploading Parquer to  {S3_DEST_PATH}...")
        wr.s3.to_parquet(
            df=df,
            path=S3_DEST_PATH,
            dataset=True,
            mode="overwrite_partitions"
            # Only deletes the paths of partitions that should be updated and then writes the new partitions files
        )

        return {
            'statusCode': 200,
            'body': json.dumps(f'Success! Parquet created in {S3_DEST_PATH}')
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