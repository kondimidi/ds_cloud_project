CREATE EXTERNAL TABLE IF NOT EXISTS vehicle_sales_parquet (
    release_year int,
    make string,
    model string,
    car_trim string,
    body string,
    transmission string,
    vin string,
    state string,
    condition double,
    odometer double,
    color string,
    interior string,
    seller string,
    mmr double,
    sellingprice double,
    saledate string
)
PARTITIONED BY (year int, month int)
STORED AS PARQUET
LOCATION 's3://konrad-ds-project-data/refined_data/'
TBLPROPERTIES ('parquet.compress'='SNAPPY');

MSCK REPAIR TABLE vehicle_sales_parquet;