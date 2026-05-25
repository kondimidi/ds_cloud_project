import time
import io
import boto3
import pandas as pd
from visualize_data import create_visualizations

# Configuration
DATABASE = "default"
VIEW_NAME = "v_vehicle_sales_clean"

def get_data_from_athena():
    print(f"Fetching data from Athena view: {VIEW_NAME}...")

    # Sending query, downloading S3's data and creating DataFrame
    query = f"SELECT * FROM {VIEW_NAME} WHERE sale_price IS NOT NULL"

    # Where to save in S3
    S3_OUTPUT_PATH = "s3://konrad-ds-project-data/athena-results/"

    athena = boto3.client('athena')
    s3 = boto3.client('s3')

    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': DATABASE},
        ResultConfiguration={'OutputLocation': S3_OUTPUT_PATH}
    )
    query_execution_id = response['QueryExecutionId']

    while True:
        status = athena.get_query_execution(QueryExecutionId=query_execution_id)
        state = status['QueryExecution']['Status']['State']
        
        if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        
        print("Waiting for query to complete...")
        time.sleep(2)

    if state != 'SUCCEEDED':
        reason = status['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
        raise Exception(f"Athena query failed with status '{state}'. Reason: {reason}")

    print("Query finished successfully. Downloading results from S3...")

    output_file_uri = status['QueryExecution']['ResultConfiguration']['OutputLocation']
    
    s3_path = output_file_uri.replace("s3://", "").split("/", 1)
    bucket_name = s3_path[0]
    key = s3_path[1]

    s3_response = s3.get_object(Bucket=bucket_name, Key=key)
    df = pd.read_csv(io.BytesIO(s3_response['Body'].read()))
    
    return df

def run_analysis():
    df = get_data_from_athena()
    create_visualizations(df)

if __name__ == "__main__":
    # 1. Downloading data
    df = get_data_from_athena()

    # 2. Simple analysis
    print("\n--- DATA PREVIEW ---")
    print(df.head())

    print("\n--- BASIC STATISTICS ---")
    # Checking mean sales price and market value (MMR)
    stats = df[['market_value', 'sale_price']].describe()
    print(stats)

    # Creating new column: price difference
    df['price_diff'] = df['sale_price'] - df['market_value']

    print("--- TOP 5 OVERPRICED MAKE (Avg Difference) ---")
    avg_diff_by_make = df.groupby('make')['price_diff'].mean().sort_values(ascending=False)
    print(avg_diff_by_make.head())

    # 3. Data visualization
    create_visualizations(df)