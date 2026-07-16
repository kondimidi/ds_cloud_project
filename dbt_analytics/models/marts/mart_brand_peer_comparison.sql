WITH trimmed_data AS (
    SELECT
        make,
        sellingprice,
        PERCENT_RANK() OVER (PARTITION BY make ORDER BY sellingprice) AS price_rank
    FROM {{ ref('stg_vehicle_sales')}}
)
SELECT
    make,
    ROUND(AVG(sellingprice), 2) AS clean_avg_price,
    COUNT(*) AS total_offers
FROM trimmed_data
WHERE price_rank BETWEEN 0.005 AND 0.995
GROUP BY 1