SELECT
    make,
    sale_year,
    COUNT(*) AS total_sales_volume,
    ROUND(AVG(sellingprice), 2) AS average_selling_price,
    ROUND(AVG(car_age), 1) AS average_car_age,
    ROUND(AVG(condition), 4) AS average_condition
FROM {{ ref('stg_vehicle_sales') }}
GROUP BY 1, 2