import boto3
import os
from botocore.exceptions import NoCredentialsError

def upload_to_s3(local_file, bucket, s3_file):
    """
    Uploads a file to an AWS S3 bucket.
    """
    s3 = boto3.client('s3')

    try:
        print(f"Uploading {local_file} to bucket {bucket}...")
        s3.upload_file(local_file, bucket, s3_file)
        print("Upload Successful!")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False

if __name__ == "__main__":
    # Define your variables
    BUCKET_NAME = 'konrad-ds-project-data'  # Replace with your actual bucket name
    LOCAL_FILE_PATH = 'data/car_prices.csv' # Check your actual filename in data/ folder
    S3_FILE_NAME = 'raw_data/car_prices_v1.csv' # How it will be named in S3

    upload_to_s3(LOCAL_FILE_PATH, BUCKET_NAME, S3_FILE_NAME)