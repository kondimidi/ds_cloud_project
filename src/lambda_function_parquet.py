import os
import json
import boto3
from datetime import datetime, timedelta
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

        # 3. Delete old month and upload new as Parquet
        # Calculate the previous month
        today = datetime.now()
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

        print(f"Uploading Parquer to  {S3_DEST_PATH}...")
        wr.s3.to_parquet(
            df=df,
            path=S3_DEST_PATH,
            dataset=True,
            mode="overwrite_partitions"
            # Only deletes the paths of partitions that should be updated and then writes the new partitions files
        )

        # 4. Repair Glue Catalog table
        athena = boto3.client('athena')
        athena.start_query_execution(
            QueryString="MSCK REPAIR TABLE vehicle_sales_parquet",
            QueryExecutionContext={'Database': 'vehicle_sales_db'},
            ResultConfiguration={'OutputLocation': f"s3://{BUCKET_NAME}/athena-results/"}
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