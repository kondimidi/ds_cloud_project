# Vehicle Sales Analysis Pipeline (AWS + Python)

## Project Overview
Automated data pipeline that fetches vehilce sales data, store it in the cloud, and performs SQL-based analysis.

## Tech Stack
- **Python**: Core logic and analysis (Pandas, Boto3 AWS Wrangler).
- **AWS S3**: Raw data storage.
- **AWS Athena**: Serverless SQL engine for querying data.
- **Git**: Version control with feature-branching workflow.
- **Kaggle API**: Data source.

## Data Pipeline
1. `download_data.py`: Fetches data from Kaggle.
2. `upload_to_s3.py`: Transfer CSV to AWS S3 bucket.
3. **AWS Athena**: SQL Views clean and cast data types.
4. `analyze_data.py`: Connects Python to Athena and generates insights.

## Key Insights
![Top Makes Chart](reports/top_makes_prices.png)
*Example: Analysis shows that Airstream (RVs) dominates average prices, followed by luxury brands.*

## How to run
1. Clone the repo.
2. Set up AWS credentials in your environment.
3. Run `pip install -r requirements.txt`.
4. Execute `python run_pipeline.py`.