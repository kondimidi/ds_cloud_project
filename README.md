# 🚗 Vehicle Sales Analytics Pipeline

[![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)

> **End-to-End Data Engineering project** that automates ingestion, transformation, and visualization of vehicle sales data using a serverless AWS architecture.

🔗 **[Live Dashboard Demo](https://dscloudproject-ykxkjvzapgrkdh4sh4q72y.streamlit.app/)**

---

## 🗺️ System Architecture



The pipeline follows a modern **Data Lakehouse** pattern:
`Kaggle API` ➔ `AWS Lambda (Ingest)` ➔ `S3 (Raw CSV)` ➔ `S3 Event` ➔ `AWS Lambda (Transform)` ➔ `S3 (Refined Parquet)` ➔ `AWS Athena` ➔ `Streamlit Cloud`

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
* Initial ingestion and SQL schema definition (`sql/create_table_vehicle_sales.sql`).
* Development of the core analysis logic in `src/analyze_data.py`.

### Phase 2: Cloud Automation (Event-Driven)
* **Incremental Loading:** Data fetched via Kaggle API and partitioned by `year/month` in S3.
* **Format Optimization:** Automatic conversion from CSV to **Apache Parquet** for 90% faster queries and lower costs.
* **Smart Monitoring:** Custom AWS SNS alerts integrated with Lambda Destinations for real-time failure notifications.
* **Serverless SQL:** Using Athena to query partitioned data directly from S3 without managing servers.

---

## 📊 Dashboard Demo

![Dashboard Demo](reports/dashboard.gif)

*The dashboard features a **Smart Buffer** logic: it fetches data once per brand selection to minimize AWS Athena costs while providing instant filtering for production years.*

---

## ⚙️ Setup & Installation

### 1. Prerequisites
* AWS Account with CLI configured.
* Kaggle API Token (`KAGGLE_USERNAME`, `KAGGLE_KEY`).

### 2. AWS Environment Variables
Set these variables in your Lambda functions:
* `BUCKET_NAME`: Target S3 bucket name.
* `SNS_TOPIC_ARN`: ARN for failure alerts.
* `KAGGLE_USERNAME` / `KAGGLE_KEY`: For data ingestion.

### 3. Local Run
```bash
# Clone the repo
git clone [https://github.com/twoja-nazwa-uzytkownika/nazwa-repozytorium.git](https://github.com/twoja-nazwa-uzytkownika/nazwa-repozytorium.git)

# Install dependencies
pip install -r requirements.txt

# Run local pipeline
python run_pipeline.py