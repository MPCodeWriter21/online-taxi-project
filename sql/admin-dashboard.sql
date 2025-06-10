--------------------------------------------------------------------------------
-- 3. Admin Dashboard
--------------------------------------------------------------------------------

-- 3.1. Manage Tariffs
UPDATE tariffs
SET price_per_km = $1
WHERE city_id = $2 AND trip_type = $3;


-- 3.2. View Pending Driver Applications
SELECT
    da.id AS application_id,
    u.name,
    u.phone,
    da.status,
    d.type AS document_type,
    f.file_path
FROM
    driver_applications da
JOIN
    users u ON da.user_id = u.id
LEFT JOIN
    documents d ON u.id = d.user_id
LEFT JOIN
    files f ON d.file_id = f.id
WHERE
    da.status = 'pending';


-- 3.3. Manage Driver Applications: Accept or Reject
-- a) Accept Driver Application
-- Step 1: Update application status and assign admin
UPDATE driver_applications SET status = 'accepted', admin_id = $1, review_date = CURRENT_TIMESTAMP WHERE id = $2;
-- Step 2: Add user to drivers table
INSERT INTO drivers (user_id, approval_status) VALUES ($3, 'approved'); -- $3 is the user_id

-- b) Reject Driver Application
UPDATE driver_applications SET status = 'rejected', admin_id = $1, review_date = CURRENT_TIMESTAMP WHERE id = $2;


-- 3.4. View Transactions in a Date Range
SELECT
    t.id AS transaction_id,
    u.name AS user_name,
    t.amount,
    t.type,
    t.date
FROM
    transactions t
JOIN
    users u ON t.user_id = u.id
WHERE
    t.date BETWEEN $1 AND $2
ORDER BY
    t.date DESC;


-- 3.5. Real-time Location Tracking: View Drivers' Locations
SELECT
    u.name AS driver_name,
    d.user_id AS driver_id,
    ST_AsText(dl.current_location) AS location,
    dl.recorded_at
FROM
    driver_locations dl
JOIN
    drivers d ON dl.driver_id = d.user_id
JOIN
    users u ON d.user_id = u.id
WHERE
    dl.recorded_at > NOW() - INTERVAL '5 minutes'; -- Drivers active in the last 5 minutes


-- 3.6. Passengers Report
-- a) Number of trips per passenger this month
SELECT
    u.name,
    COUNT(t.id) AS monthly_trip_count
FROM
    trips t
JOIN
    users u ON t.passenger_id = u.id
WHERE
    t.trip_status = 'completed' AND
    t.start_time >= date_trunc('month', CURRENT_DATE)
GROUP BY
    u.id, u.name
ORDER BY
    monthly_trip_count DESC;

-- b) List of top 10 passengers by total payment
SELECT
    u.name,
    SUM(p.amount) AS total_payment
FROM
    payments p
JOIN
    trips t ON p.id = t.payment_id
JOIN
    users u ON t.passenger_id = u.id
WHERE
    p.status = 'completed'
GROUP BY
    u.id, u.name
ORDER BY
    total_payment DESC
LIMIT 10;


-- 3.7. Active Drivers Report
-- Includes total trips, urban and intercity trips, and average rating
SELECT
    u.name AS driver_name,
    d.user_id,
    COUNT(t.id) AS total_trips,
    SUM(CASE WHEN t.trip_type = 'urban' THEN 1 ELSE 0 END) AS urban_trips,
    SUM(CASE WHEN t.trip_type = 'intercity' THEN 1 ELSE 0 END) AS intercity_trips,
    AVG(f.rating) AS average_rating
FROM
    drivers d
JOIN
    users u ON d.user_id = u.id
LEFT JOIN
    trips t ON d.user_id = t.driver_id AND t.trip_status = 'completed'
LEFT JOIN
    feedbacks f ON t.id = f.trip_id
GROUP BY
    d.user_id, u.name
ORDER BY
    total_trips DESC;


-- 3.8. Trip Routes Report
SELECT
    t.route_id,
    EXTRACT(HOUR FROM t.start_time) AS hour_of_day,
    COUNT(t.id) AS trip_count
FROM
    trips t
WHERE
    t.route_id IS NOT NULL
GROUP BY
    t.route_id, hour_of_day
ORDER BY
    trip_count DESC, hour_of_day;
