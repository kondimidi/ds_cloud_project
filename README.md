# Vehicle Sales Analysis Pipeline (AWS + Python)

## Project Overview
Automated data pipeline that fetches vehicle sales data, store it in the cloud, performs SQL-based analysis and shows metrics in the online dashboard.

## Tech Stack
- **Python**: Core logic and analysis (Pandas, Boto3 AWS Wrangler).
- **AWS S3**: Scalable storage for Raw (CSV) and Refined (Parquet) Data Zones.
- **AWS Glue**: Used as a Data Catalog to store table metadata and manage partitions.
- **AWS Athena**: Serverless SQL engine for high-performance querying.
- **AWS Lambda**: Serverless compute for automated data ingestion and transformation.
- **Amazon EventBridge**: Pipeline scheduling via CRON rules.
- **AWS SNS**: Monitoring and email alerts for pipeline failures.
- **Git**: Version control with feature-branching workflow.
- **Kaggle API**: Source for vehicle sales datasets.
- **Streamlit**: Cloud dashboard for datasets metrics.

### Phase 1: Local Prototype & SQL Setup
This initial phase focused on building the core logic and defining the database schema:
1. `src/download_data.py`: Fetches raw data from Kaggle to local storage.
2. `src/upload_to_s3.py`: Transfers CSV files to the AWS S3 `raw_data/` zone.
3. `sql/create_table_vehicle_sales.sql`: Defines the initial schema for raw CSV data.
4. `src/analyze_data.py`: Connects Python to Athena to generate business insights.
5. `run_pipeline.py`: Orchestrates the local execution of the entire flow.

### Phase 2: Cloud Automation (Event-Driven Architecture)
#### Architecture schema: 
- `Kaggle API` -> `Lambda (Ingestion)` -> `S3 (Raw)` -> `Lambda (Transformation)` -> `S3 (Refined/Parquet)` -> `Athena` -> `Streamlit`

The project was scaled to AWS to ensure data freshness and cost optimization:
1. **Ingestion (`src/lambda_function.py`)**: Triggered by **EventBridge (CRON)**. Fetches data via Kaggle API and saves it in the **Raw Zone** (`raw_data/{date}/`) using **Incremental Loading**.
    * **Runtime**: Python 3.12
    * **Timeout**: 1 minute | **Memory**: 512 MB
    * **Layers**: `AWSSDKPandas-Python312`, `kaggle-library`
2. **Transformation (`src/lambda_function_parquet.py`)**: Triggered by **S3 Event Notifications** (Prefix: `raw_data/`). Cleans data with Pandas and converts it to **Apache Parquet**.
    * **Runtime**: Python 3.12
    * **Timeout**: 2 minutes | **Memory**: 1024 MB
    * **Layers**: `AWSSDKPandas-Python312`
3. **Custom Layer Creation**: To use the Kaggle API in Lambda, create a custom layer:
```bash
mkdir -p kaggle_layer/python
cd kaggle_layer/python
pip install kaggle -t .
cd ..
zip -r kaggle_layer.zip python
aws lambda publish-layer-version --layer-name kaggle-library --zip-file fileb://kaggle_layer.zip --compatible-runtimes python3.12
```
4. **Partitioning**: Data is stored in the Refined Zone (refined_data/) partitioned by year and month (e.g., year=2026/month=2/) for optimized query performance.
5. **Monitoring (AWS SNS)**: Instant email alerts on failure, managed via Lambda Destinations and internal error handling:
```python
sns.publish(
    TopicArn=os.environ.get('SNS_TOPIC_ARN'),
    Message=f"Lambda failed: {str(e)}",
    Subject="PIPELINE ERROR ALERT"
)
```
6. **Permissions**: The Lambda execution role requires AmazonS3FullAccess, AmazonAthenaFullAccess, and AWSGlueConsoleFullAccess.
7. `sql/create_table_vehicle_sales_parquet.sql`: SQL DDL for the optimized Parquet-based partitioned table.

## Key Insights
![Top Makes Chart](reports/top_makes_prices.png)
*Example: Analysis shows that Airstream (RVs) dominates average prices, followed by luxury brands.*

## Dashboard's demo
![Dahboard's video](reports/dashboard.gif)

*Live Demo: [LINK](https://dscloudproject-ykxkjvzapgrkdh4sh4q72y.streamlit.app/).*

## How to run
1. Clone the repo.
2. Set up AWS credentials in your environment.
3. Set up Kaggle credentials (KAGGLE_USERNAME and KAGGLE_KEY). Obtain these from Kaggle Account settings -> Create New API Token.
4. AWS Environment Variables: Set the following variables in your Lambda functions:
- BUCKET_NAME: main directory in general S3 bucket (`lambda_function.py`, `lambda_function_parquet.py`),
- KAGGLE_USERNAME & KAGGLE_KEY (`lambda_function.py`),
- SNS_TOPIC_ARN: The ARN of your SNS topic for alerts (`lambda_function.py`, `lambda_function_parquet.py`).
5. Run `pip install -r requirements.txt`.
6. **Local execution**: Run `python run_pipeline.py`.
7. **Cloud deployment**: Zip files and Layers are provided to deploy as AWS Lambda functions.