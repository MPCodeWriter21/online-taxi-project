------------------------
-- 2. Driver Dashboard
------------------------

-- 2.1. Driver Registration
-- a) Submit Driver Application
INSERT INTO driver_applications (user_id, status)
VALUES ($1, 'pending');

-- b) Upload Required Documents
INSERT INTO documents (user_id, type, file_id, status)
VALUES ($1, $2, $3, 'pending');


-- 2.2. Show Nearby Trip Requests
SELECT
    t.id AS trip_id,
    t.start_location,
    t.end_location,
    t.trip_type,
    u.name AS passenger_name,
    ST_Distance(t.start_location, ST_SetSRID(ST_MakePoint($1, $2), 4326)) AS distance
FROM
    trips t
JOIN
    users u ON t.passenger_id = u.id
WHERE
    t.trip_status = 'pending'
    AND ST_DWithin(
        t.start_location,
        ST_SetSRID(ST_MakePoint($1, $2), 4326),
        5000 -- Radius of 5 kilometers
    )
ORDER BY
    distance;


-- 2.3. Accept or Reject a Trip Request
-- a) Accept Trip Request
UPDATE trips
SET trip_status = 'started', driver_id = $1
WHERE id = $2 AND trip_status = 'pending';

-- b) Reject Trip Request: No need for a specific query, just ignore the request.


-- 2.4. Update Trip Status by Driver
UPDATE trips
SET trip_status = 'completed', end_time = CURRENT_TIMESTAMP
WHERE id = $1 AND driver_id = $2;
