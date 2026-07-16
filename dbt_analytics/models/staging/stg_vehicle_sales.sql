WITH prepared_data AS (
    SELECT
        vin,
        make,
        model AS car_model,
        body AS body_type,
        state,
        condition,
        odometer,
        color,
        saledate,
        sellingprice,
        release_year,
        YEAR(TRY(parse_datetime(saledate, 'E MMM dd yyyy HH:mm:ss ''GMT''Z (z)'))) AS sale_year
    FROM {{ source('athena_source', 'vehicle_sales_parquet') }}
)
SELECT 
    vin, make, car_model, body_type, state, condition, odometer, color, saledate, sellingprice, sale_year,
    GREATEST(sale_year - release_year, 0) AS car_age
FROM prepared_data
WHERE sale_year IS NOT NULL