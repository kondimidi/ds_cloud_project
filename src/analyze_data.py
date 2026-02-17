import awswrangler as wr
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
    S3_OUTPU_PATH = "s3://konrad-ds-project-data/athena-results/"

    df = wr.athena.read_sql_query(
        sql=query,
        database=DATABASE,
        s3_output = S3_OUTPU_PATH # Says to wrangler where to put results
    )
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