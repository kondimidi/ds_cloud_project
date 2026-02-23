DROP TABLE IF EXISTS vehicle_sales;

CREATE EXTERNAL TABLE IF NOT EXISTS vehicle_sales (
    `year` string,
    make string,
    model string,
    car_trim string,
    body string,
    transmission string,
    vin string,
    state string,
    condition string,
    odometer string,
    `color` string,
    interior string,
    seller string,
    mmr string,
    sellingprice string,
    saledate string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  'separatorChar' = ',',
  'quoteChar' = '\"',
  'escapeChar' = '\\'
)
LOCATION 's3://konrad-ds-project-data/raw_data/'
TBLPROPERTIES (
  'has_encrypted_data'='false', 
  'skip.header.line.count'='1',
  'use.null.for.invalid.data' = 'true');

CREATE OR REPLACE VIEW v_vehicle_sales_clean AS
SELECT
    TRY_CAST(year as INT) as release_year,
    make,
    model,
    car_trim,
    body,
    transmission,
    state,
    TRY_CAST(NULLIF(condition, '') AS INT) as condition_score,
    TRY_CAST(NULLIF(odometer, '') AS DOUBLE) as mileage,
    color,
    TRY_CAST(NULLIF(mmr, '') AS DECIMAL(12,2)) as market_value,
    TRY_CAST(NULLIF(sellingprice, '') AS DECIMAL(12,2)) as sale_price,
    saledate
FROM vehicle_sales;
