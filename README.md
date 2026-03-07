# 🚗 Vehicle Sales Analytics Pipeline

[![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)

> **End-to-End Data Engineering project** that automates ingestion, transformation, and visualization of vehicle sales data using a serverless AWS architecture.

🔗 **[Live Dashboard Demo](https://dscloudproject-ykxkjvzapgrkdh4sh4q72y.streamlit.app/)**

---

## 🗺️ System Architecture

```mermaid
graph LR
	A[Kaggle API] -- Cron Every Month --> B(Lambda Ingest)
	B --> C{S3 Raw Zone}
	C -- S3 Event --> D(Lambda Transform)
	D --> E{S3 Refined Zone}
	E --> F[AWS Glue Catalog]
	F --> G[AWS Athena]
	G --> H[Streamlit Cloud]
	
	subgraph Monitoring
	D -.-> I[AWS SNS Email]
	end

	subgraph Storage Optimization
	E -.-> J[Parquet Format]
	end

---

## 🛠️ Tech Stack

* **Compute:** AWS Lambda (Serverless Python 3.12)
* **Storage:** AWS S3 (Raw & Refined Zones)
* **Orchestration:** Amazon EventBridge (Cron) & S3 Event Notifications
* **Data Catalog & Query:** AWS Glue, AWS Athena (SQL)
* **Monitoring:** AWS SNS (Email Alerts)
* **Visualization:** Streamlit Cloud, Pandas, Matplotlib/Seaborn
* **CI/CD & Tools:** Git (Feature-branching), Kaggle API

---

## 🚀 Key Features

### Phase 1: Local Prototype
This initial phase focused on building the core logic and defining the database schema:
1. `src/download_data.py`: Fetches raw data from Kaggle to local storage.
2. `src/upload_to_s3.py`: Transfers CSV files to the AWS S3 `raw_data/` zone.
3. `src/analyze_data.py`: Connects Python to Athena to generate business insights.
4. `run_pipeline.py`: Orchestrates the local execution of the entire flow.

### Phase 2: Automated Serverless Pipeline
This next phase focused on recreating the process of the first one in the order to be manage by AWS environment.
1. **Ingestion (`src/lambda_function.py`)**: Triggered by **EventBridge (CRON)**. 
    * Fetches incremental data via Kaggle API and saves it in the **Raw Zone** (`raw_data/{date}/`) using **Incremental Loading**.
    * **Automation**: Uses a custom Lambda Layer for the `kaggle` library.
2.  **Transformation & Hygiene (`src/lambda_function_parquet.py`)**: Triggered by **S3 Events**.
    * **Data Cleaning**: Standardizes vehicle makes to *Title Case* and handles whitespaces.
    * **Format Optimization**: Converts CSV to **Apache Parquet** for cost reduction in queries.
    * **Self-Cleaning**: Automatically purges old partitions to maintain data idempotency.
3.  **Metadata Sync**: Uses `MSCK REPAIR TABLE` via Boto3 to keep the Glue Catalog synchronized with S3 automatically.
4.  **Monitoring**: Integrated **AWS SNS** for instant email alerts on pipeline failures via Lambda Destinations.

---

## 💰 Cost Optimization & Management
A strategic decision was made to use a **Serverless Data Lake** instead of a traditional RDS instance:

* **Athena vs. RDS**: By choosing Athena, the project avoids the fixed 24/7 costs of an RDS/Aurora instance.
* **Lifecycle Policies**: Automated S3 Lifecycle rules expire `athena-results/` every 7 days (`raw_data/` every 30 days), preventing storage clutter.
* **Budgeting**: **AWS Budgets** implemented with email triggers to monitor the credit utilization and prevent unexpected billing.

### Phase 3: Data Visualization & Serving
Developed a serverless dashboard using Streamlit Cloud with two architectural approaches:
1. **Cloud-Heavy Approach (`src/dashboard_cloud_heavy.py`)**: 
   * Delegates all aggregations to AWS Athena. 
   * **Best for:** Massive datasets (Big Data) where local RAM is insufficient.
   * **Trade-off:** Higher AWS costs due to frequent S3 scanning.
2. **Smart Buffer Approach (`src/dashboard_smart_buffer.py`)**: 
   * Fetches full brand data into a Pandas DataFrame and performs sub-filtering locally.
   * **Best for:** Optimal User Experience and cost reduction.
   * **Trade-off:** Requires more RAM on the hosting server.
3. **Data Cleaning at Source**: Implemented Trino-compatible SQL logic to filter out `NULL/Nan` values directly in Athena, ensuring clean data ingestion into the UI.
4. **Athena Staging**: Results of all dashboard queries are managed in: `s3://konrad-ds-project-data/athena-results/`.

---

## 📊 Dashboard Demo

![Dashboard Demo](reports/dashboard.gif)

*The dashboard features a **Smart Buffer** logic: it fetches data once per brand selection to minimize AWS Athena costs while providing instant filtering for production years.*

---

## 🚀 Future Improvements

* Implement Entity Resolution using fuzzy matching (e.g., Levenshtein distance) to unify brand names like 'VW' and 'Volkswagen'.
* Integrate a Machine Learning model to predict vehicle prices based on mileage and condition.

## ⚙️ Setup & Installation

### 1. Prerequisites
* AWS Account with CLI configured.
* Kaggle API Token (`KAGGLE_USERNAME`, `KAGGLE_KEY`).

### 2. AWS Environment Variables
Set these variables in your Lambda functions:
* `BUCKET_NAME`: Target S3 bucket name (`lambda_function.py`, `lambda_function_parquet.py`).
* `SNS_TOPIC_ARN`: ARN for failure alerts (`lambda_function.py`, `lambda_function_parquet.py`).
* `KAGGLE_USERNAME` / `KAGGLE_KEY`: For data ingestion (`lambda_function.py`). Obtain these from Kaggle Account settings -> Create New API Token. 
* `S3_STAGING_DIR`: The S3 path where Athena will store query results (e.g., s3://your-bucket-name/athena-results/).

### 3. Lambda requirements
* **Runtime**: Python 3.12
* **Timeout**: 2 minute | **Memory**: 1024 MB
* **Layers**: `AWSSDKPandas-Python312`, `kaggle-library`
* **Permissions**: AmazonS3FullAccess, AmazonAthenaFullAccess, and AWSGlueConsoleFullAccess.

### 4. **Custom Layer Creation**: To use the Kaggle API in Lambda, create a custom layer:
```bash
mkdir -p kaggle_layer/python
cd kaggle_layer/python
pip install kaggle -t .
cd ..
zip -r kaggle_layer.zip python
aws lambda publish-layer-version --layer-name kaggle-library --zip-file fileb://kaggle_layer.zip --compatible-runtimes python3.12
```

### 5. Other
* `sql/create_table_vehicle_sales_parquet.sql`: SQL DDL for the optimized Parquet-based partitioned table.
* `sql/create_table_vehicle_sales.sql`: Defines the initial schema for raw CSV data.