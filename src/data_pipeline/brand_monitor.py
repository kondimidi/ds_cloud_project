import os
import json
import time
import boto3

CANONICAL_BRANDS = set(["Ford", "Chevrolet", "Nissan", "Toyota", "Dodge", "Honda",
                  "Hyundai", "Bmw", "Kia", "Chrysler", "Mercedes-Benz", "Jeep",
                  "Infiniti", "Volkswagen", "Lexus", "Gmc", "Uknown", "Mazda",
                  "Cadillac", "Acura", "Audi", "Lincoln", "Buick", "Subaru",
                  "Ram", "Pontiac", "Mitsubishi", "Volvo", "Mini", "Saturn",
                  "Mercury", "Land Rover", "Scion", "Jaguar", "Porsche",
                  "Suzuki", "Fiat", "Hummer", "Saab", "Smart", "Oldsmobile",
                  "Isuzu", "Maserati", "Bentley", "Plymouth", "Aston Martin",
                  "Tesla", "Ferrari", "Geo", "Rolls-Royce", "Fisker",
                  "Lamborghini", "Daewoo", "Lotus", "Airstream"])

def lambda_handler(event, context):
    athena = boto3.client('athena')
    sns = boto3.client('sns')

    # Get parameters from Step Functions
    year = event('year')
    month = event('month')
    bucket = os.environ.get('BUCKET_NAME')
    sns_topic = os.environ.get('SNS_TOPIC_ARN')
    
    # 1. Query to get distinct brands for current partition
    query = f"""
        SELECT DISTINCT make 
        FROM vehicle_sales_db.vehicle_sales_parquet 
        WHERE year = {year} AND month = {month};
    """
    
    # 2. Run Athena Query
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': 'vehicle_sales_db'},
        ResultConfiguration={'OutputLocation': f"s3://{bucket}/athena-results/"}
    )
    query_execution_id = response['QueryExecutionId']
    
    # 3. Wait for query to complete (Polling)
    while True:
        status = athena.get_query_execution(QueryExecutionId=query_execution_id)['QueryExecution']['Status']['State']
        if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        time.sleep(1)
        
    if status != 'SUCCEEDED':
        raise Exception(f"Athena drift query failed with status: {status}")
        
    # 4. Get Results
    results = athena.get_query_results(QueryExecutionId=query_execution_id)
    present_brands = set()
    
    # Parse rows (skip header row)
    for row in results['ResultSet']['Rows'][1:]:
        brand_name = row['Data'][0].get('VarCharValue')
        if brand_name:
            present_brands.add(brand_name)
            
    # 5. Check for Drift (New Brands)
    new_brands = list(present_brands - CANONICAL_BRANDS)
    
    # 6. Action if drift detected
    if new_brands:
        message = f"""
        DATA DRIFT ALERT - NEW BRANDS DETECTED!
        
        The pipeline for {year}-{month:02d} found new vehicle brands that are NOT in your canonical dictionary!
        
        New brands detected: {new_brands}
        
        Action required: Update 'canonical_mark' list in your transformation Lambda and retraining scripts to include these brands.
        """
        
        sns.publish(
            TopicArn=sns_topic,
            Message=message,
            Subject="📊 AWS Pipeline: Data Drift Detected"
        )
        print(f"Alert sent! Found new brands: {new_brands}")
    else:
        print("No data drift detected. All brands are canonical.")
        
    return {
        "statusCode": 200,
        "new_brands_found": new_brands
    }