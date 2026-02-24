# Vehicle Sales Analysis Pipeline (AWS + Python)

## Project Overview
Automated data pipeline that fetches vehicle sales data, store it in the cloud, and performs SQL-based analysis.

## Tech Stack
- **Python**: Core logic and analysis (Pandas, Boto3 AWS Wrangler).
- **AWS S3**: Scalable storage for Raw (CSV) and Refined (Parquet) Data Zones.
- **AWS Athena**: Serverless SQL engine for high-performance querying.
- **AWS Lambda**: Serverless compute for automated data ingestion and transformation.
- **Amazon EventBridge**: Pipeline scheduling via CRON rules.
- **AWS SNS**: Monitoring and email alerts for pipeline failures.
- **Git**: Version control with feature-branching workflow.
- **Kaggle API**: Source for vehicle sales datasets.

### Phase 1: Local Prototype & SQL Setup
This initial phase focused on building the core logic and defining the database schema:
1. `src/download_data.py`: Fetches raw data from Kaggle to local storage.
2. `src/upload_to_s3.py`: Transfers CSV files to the AWS S3 `raw_data/` zone.
3. `sql/create_table_vehicle_sales.sql`: Defines the initial schema for raw CSV data.
4. `src/analyze_data.py`: Connects Python to Athena to generate business insights.
5. `run_pipeline.py`: Orchestrates the local execution of the entire flow.

### Phase 2: Cloud Automation (Event-Driven Architecture)
The project was scaled to AWS to ensure data freshness and cost optimization:
1. **Ingestion (`src/lambda_function.py`)**: Triggered by **EventBridge (CRON)**. It fetches data and saves it in the **Raw Zone** using **Incremental Loading** (timestamped folders). Set the Timeout to 1 minute. Used layer: AWSSDKPandas-Python312.
2. **Transformation (`src/lambda_function_parquet.py`)**: Triggered by **S3 Event Notifications (Prefix: raw_data/)**. It cleans the data and converts it to **Apache Parquet**. Set the Timeout to 2 minutes and the **Memory** to 1024 MB. Used layers: AWSSDKPandas-Python312 and kaggle-library (setting below).
	```mkdir -p kaggle_layer/python
	cd kaggle_layer/python
	pip install kaggle -t .
	cd ..
	zip -r kaggle_layer.zip python
	aws lambda publish-layer-version --layer-name kaggle-library --zip-file fileb://kaggle_layer.zip --compatible-runtimes python3.12```
3. **Partitioning**: Data is saved in the **Refined Zone** (`refined_data/`) partitioned by `year` and `month` for query speed and cost reduction.
4. `sql/create_table_vehicle_sales_parquet.sql`: SQL DDL for the optimized Parquet-based partitioned table.
5. **Monitoring**: **AWS SNS** sends instant email alerts if any stage fails.
6. **Permissions**: Ensure the Lambda execution role has AmazonS3FullAccess, AmazonAthenaFullAccess, and AWSGlueConsoleFullAccess policies attached.

## Key Insights
![Top Makes Chart](reports/top_makes_prices.png)
*Example: Analysis shows that Airstream (RVs) dominates average prices, followed by luxury brands.*

## How to run
1. Clone the repo.
2. Set up AWS credentials in your environment.
3. Set up Kaggle credentials (KAGGLE_USERNAME and KAGGLE_KEY). Obtain these from Kaggle Account settings -> Create New API Token.
4. Run `pip install -r requirements.txt`.
5. **Local execution**: Run `python run_pipeline.py`.
6. **Cloud deployment**: Zip files and Layers are provided to deploy as AWS Lambda functions.