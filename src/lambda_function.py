import os
import json
import boto3

# 1. It has to be here BEFORE anything else happens
os.environ['KAGGLE_CONFIG_DIR'] = "/tmp"


def lambda_handler(event, context):
    # PARAMETERS
    BUCKET_NAME = 'konrad-ds-project-data'
    DATASET_NAME = 'syedanwarafridi/vehicle-sales-data'
    TEMP_FILE = '/tmp/car_prices.csv'
    S3_KEY = 'raw_data/car_prices.csv'

    # Kaggle supports these environmental variables directly:
    os.environ['KAGGLE_USERNAME'] = os.environ.get('KAGGLE_USERNAME')
    os.environ['KAGGLE_KEY'] = os.environ.get('KAGGLE_KEY')

    try:
        # 2. WE IMPORT KAGGLE ONLY HERE (Lazy Import)
        # Thanks to this, the environment variables are already set in the system.
        import kaggle
        print("Kaggle API authenticated successfully via env vars.")

        # 3. Download from Kaggle
        print(f"Downloading dataset {DATASET_NAME}...")
        # unzip=True rozpakuje plik do /tmp
        kaggle.api.dataset_download_files(DATASET_NAME, path='/tmp', unzip=True)

        # We check what has been downloaded (just to be sure)
        files = os.listdir('/tmp')
        print(f"Files in /tmp: {files}")

        # 4. Send to S3
        s3 = boto3.client('s3')
        # We are looking for a .csv file in /tmp (in case the name is different)
        csv_files = [f for f in files if f.endswith('.csv')]

        if not csv_files:
            raise Exception("No CSV file found in /tmp after download!")

        file_to_upload = os.path.join('/tmp', csv_files[0])
        print(f"Uploading {file_to_upload} to S3...")

        s3.upload_file(file_to_upload, BUCKET_NAME, S3_KEY)

        return {
            'statusCode': 200,
            'body': json.dumps('Pipeline SUCCESS! Data updated in S3.')
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Pipeline failed: {str(e)}")
        }