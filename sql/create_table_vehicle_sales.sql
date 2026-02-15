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