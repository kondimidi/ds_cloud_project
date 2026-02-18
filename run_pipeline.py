import os
from src.download_data import download_dataset
from src.upload_to_s3 import upload_to_s3
from src.analyze_data import run_analysis

def run_everything():
    # 1. Confugiration
    KAGGLE_DATASET = 'syedanwarafridi/vehicle-sales-data'
    LOCAL_DATA_DIR = './data'
    BUCKET_NAME = 'konrad-ds-project-data'
    S3_TARGET_NAME = 'raw_data/car_prices.csv'

    # Find the name of the file that Kaggle will download
    LOCAL_FILE_PATH = os.path.join(LOCAL_DATA_DIR, 'car_prices.csv')

    print("--- STEP 1: DOWNLOADING DATA ---")
    download_dataset(KAGGLE_DATASET, LOCAL_DATA_DIR)

    print("\n--- STEP 2: UPLOADING TO AWS S# ---")
    if os.path.exists(LOCAL_FILE_PATH):
        success = upload_to_s3(LOCAL_FILE_PATH, BUCKET_NAME, S3_TARGET_NAME)
        if success:
            print("\nPIPELINE COMPLETED SUCCESSFULLY!")
    else:
        print(f"Error: File {LOCAL_FILE_PATH} not found. Check the file name in data/ folder.")

    print("\n--- STEP 3: ANALYZING AND VISUALIZING ---")
    run_analysis()

if __name__ == "__main__":
    run_everything()