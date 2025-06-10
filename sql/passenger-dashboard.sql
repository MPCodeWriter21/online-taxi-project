---------------------------
-- 1. Passenger Dashboard
---------------------------

-- 1.1. Registration and Authentication
INSERT INTO users (name, phone, email, status)
VALUES ($1, $2, $3, 'active')
RETURNING id;


-- 1.2. Request or Cancel a Trip
INSERT INTO trips (passenger_id, trip_status, trip_type, start_location, end_location)
VALUES ($1, 'pending', $2, ST_SetSRID(ST_MakePoint($3, $4), 4326), ST_SetSRID(ST_MakePoint($5, $6), 4326))
RETURNING id;

UPDATE trips
SET trip_status = 'canceled'
WHERE id = $1 AND passenger_id = $2 AND trip_status = 'pending';


-- 1.3. Log Trip Status, e.g., delay, traffic
INSERT INTO trip_status_history (trip_id, status, reason)
VALUES ($1, 'waiting', $2);


-- 1.4. Payment
INSERT INTO payments (amount, payment_type, status)
VALUES ($1, 'electronic', 'completed')
RETURNING id;

-- Connector to trips table
UPDATE trips
SET payment_id = $1, discount_code_id = $2
WHERE id = $3;


-- 1.5. Feedback and Rating
INSERT INTO feedbacks (trip_id, giver_id, receiver_id, rating, comment)
VALUES ($1, $2, $3, $4, $5); -- $1:trip_id, $2:passenger_id, $3:driver_id, $4:rating, $5:comment
