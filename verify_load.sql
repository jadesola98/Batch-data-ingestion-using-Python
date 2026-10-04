-- Checks to run in pgAdmin after a load.

-- 1. Every run, newest first: did each month succeed, and how many rows?
SELECT taxi, source_month, rows_loaded, status, error, started_at, finished_at
FROM ingestion_runs
ORDER BY started_at DESC;

-- 2. Rows per month in the table. Should match the latest successful run for each month,
--    with no month counted twice.
SELECT source_month, COUNT(*) AS trips
FROM yellow_taxi_trips
GROUP BY source_month
ORDER BY source_month;

-- 3. Pickups outside the month they were loaded for.
--    The source files contain a few mis-dated trips; this shows how many.
SELECT source_month, COUNT(*) AS trips_outside_month
FROM yellow_taxi_trips
WHERE TO_CHAR(tpep_pickup_datetime, 'YYYY-MM') <> source_month
GROUP BY source_month
ORDER BY source_month;

-- 4. Basic sanity checks: negative fares, zero distances, dropoff before pickup.
SELECT
    SUM(CASE WHEN total_amount < 0 THEN 1 ELSE 0 END)                       AS negative_totals,
    SUM(CASE WHEN trip_distance = 0 THEN 1 ELSE 0 END)                      AS zero_distance_trips,
    SUM(CASE WHEN tpep_dropoff_datetime < tpep_pickup_datetime THEN 1 ELSE 0 END) AS dropoff_before_pickup
FROM yellow_taxi_trips;
