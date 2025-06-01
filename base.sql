create extension postgis;


-- Users Table: Base for all user types (Passenger, Driver, Admin)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(100) UNIQUE,
    user_type VARCHAR(20) NOT NULL, -- ENUM: 'passenger', 'driver', 'admin'
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    wallet_balance NUMERIC(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Passengers Table (extension of users)
CREATE TABLE passengers (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Drivers Table (extension of users)
CREATE TABLE drivers (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    license_number VARCHAR(50),
    car_info JSONB,
    approval_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Admin Table (extension of users)
CREATE TABLE admins (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    access_level VARCHAR(20) DEFAULT 'normal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Cities Table
CREATE TABLE cities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    coverage_status BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Routes Table (with PostGIS geometry for start & end)
CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    start_city_id INTEGER REFERENCES cities(id),
    end_city_id INTEGER REFERENCES cities(id),
    start_location geometry(Point, 4326),
    end_location geometry(Point, 4326),
    is_urban BOOLEAN,
    distance_km NUMERIC(8,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Tariffs Table
CREATE TABLE tariffs (
    id SERIAL PRIMARY KEY,
    city_id INTEGER REFERENCES cities(id),
    trip_type VARCHAR(30), -- ENUM: 'urban', 'intercity', 'shared', 'economy'
    price_per_km NUMERIC(10,2) NOT NULL,
    effective_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Trips Table
CREATE TABLE trips (
    id SERIAL PRIMARY KEY,
    passenger_id INTEGER REFERENCES passengers(user_id),
    driver_id INTEGER REFERENCES drivers(user_id),
    route_id INTEGER REFERENCES routes(id),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    trip_status VARCHAR(30) DEFAULT 'pending', -- ENUM: 'completed', 'canceled', etc.
    trip_type VARCHAR(30),
    payment_id INTEGER,
    discount_code_id INTEGER,
    start_location geometry(Point, 4326),
    end_location geometry(Point, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Payments Table
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER REFERENCES trips(id),
    amount NUMERIC(12,2) NOT NULL,
    payment_type VARCHAR(15), -- ENUM: 'cash', 'electronic'
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Discount Codes Table
CREATE TABLE discount_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    value NUMERIC(8,2) NOT NULL,
    type VARCHAR(10) DEFAULT 'amount', -- 'amount' or 'percent'
    expiry_date DATE,
    status VARCHAR(20) DEFAULT 'active', -- ENUM: 'used', 'expired', 'active'
    assigned_to_user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Messages Table
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER REFERENCES users(id),
    receiver_id INTEGER REFERENCES users(id),
    trip_id INTEGER REFERENCES trips(id),
    content TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Feedback/Rating Table
CREATE TABLE feedbacks (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER REFERENCES trips(id),
    giver_id INTEGER REFERENCES users(id),
    receiver_id INTEGER REFERENCES users(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Driver Applications Table
CREATE TABLE driver_applications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending', -- ENUM: 'pending', 'accepted', 'rejected'
    admin_id INTEGER REFERENCES admins(user_id),
    review_date TIMESTAMP,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Documents Table
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    type VARCHAR(30), -- e.g. 'license', 'car_registration'
    file_path VARCHAR(255),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Transactions Table (for wallet & system financial operations)
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    amount NUMERIC(15,2) NOT NULL,
    type VARCHAR(20), -- 'deposit', 'withdraw', 'trip_payment', etc.
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_id INTEGER REFERENCES payments(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Trip Status History Table (Optional, for advanced status tracking)
CREATE TABLE trip_status_history (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER REFERENCES trips(id),
    status VARCHAR(30),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Indexes for performance (example)
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_drivers_status ON drivers(approval_status);
CREATE INDEX idx_trips_status ON trips(trip_status);
CREATE INDEX idx_trips_start_location ON trips USING GIST(start_location);
CREATE INDEX idx_trips_end_location ON trips USING GIST(end_location);
