create extension postgis;

-- ENUM for status in users table (assuming possible values)
CREATE TYPE user_status_enum AS ENUM ('active', 'inactive', 'banned');

-- ENUM for approval_status in drivers table
CREATE TYPE driver_approval_status_enum AS ENUM ('pending', 'approved', 'rejected');

-- ENUM for access_level in admins table (assuming possible values)
CREATE TYPE admin_access_level_enum AS ENUM ('normal', 'superuser');

-- ENUM for trip_type in tariffs and trips table
CREATE TYPE trip_type_enum AS ENUM ('urban', 'intercity', 'shared', 'economy');

-- ENUM for trip_status in trips table
CREATE TYPE trip_status_enum AS ENUM ('pending', 'completed', 'canceled', 'started', 'waiting', 'failed');

-- ENUM for payment_type in payments table
CREATE TYPE payment_type_enum AS ENUM ('cash', 'electronic');

-- ENUM for status in payments table
CREATE TYPE payment_status_enum AS ENUM ('pending', 'completed', 'failed', 'canceled');

-- ENUM for discount code type in discount_codes table
CREATE TYPE discount_code_type_enum AS ENUM ('amount', 'percent');

-- ENUM for status in discount_codes table
CREATE TYPE discount_code_status_enum AS ENUM ('used', 'expired', 'active');

-- ENUM for status in driver_applications table
CREATE TYPE driver_application_status_enum AS ENUM ('pending', 'accepted', 'rejected');

-- ENUM for document type in documents table (add as needed)
CREATE TYPE document_type_enum AS ENUM ('license', 'car_registration', 'insurance', 'identity', 'other');

-- ENUM for document status in documents table
CREATE TYPE document_status_enum AS ENUM ('pending', 'approved', 'rejected');

-- ENUM for transaction type in transactions table
CREATE TYPE transaction_type_enum AS ENUM ('deposit', 'withdraw', 'trip_payment', 'refund', 'adjustment');

-- ENUM for trip status history
CREATE TYPE trip_status_history_status_enum AS ENUM ('pending', 'started', 'waiting', 'completed', 'canceled', 'failed', 'reopened');

-- Users Table: Base for all user types (Passenger, Driver, Admin)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    wallet_balance NUMERIC(15,2) DEFAULT 0,
    status user_status_enum,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Drivers Table (extension of users)
CREATE TABLE drivers (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    license_number VARCHAR(50),
    car_info JSONB,
    approval_status driver_approval_status_enum,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Admin Table (extension of users)
CREATE TABLE admins (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    access_level admin_access_level_enum,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Cities Table
CREATE TABLE cities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    province_id INTEGER REFERENCES province(id) NOT NULL,
    coverage_status BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);


CREATE TABLE province (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
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
    is_return BOOLEAN,
    distance_km NUMERIC(8,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Tariffs Table
CREATE TABLE tariffs (
    id SERIAL PRIMARY KEY,
    city_id INTEGER REFERENCES cities(id),
    trip_type trip_type_enum,
    price_per_km NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Trips Table
CREATE TABLE trips (
    id SERIAL PRIMARY KEY,
    passenger_id INTEGER REFERENCES users(id),
    driver_id INTEGER REFERENCES drivers(user_id),
    route_id INTEGER REFERENCES routes(id),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    trip_status trip_status_enum,
    trip_type trip_type_enum,
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
    amount NUMERIC(12,2) NOT NULL,
    payment_type payment_type_enum,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status payment_status_enum,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Discount Codes Table
CREATE TABLE discount_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    value NUMERIC(8,2) NOT NULL,
    type discount_code_type_enum,
    expiry_date DATE,
    status discount_code_status_enum, -- ENUM: 'used', 'expired', 'active'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Mapping table to assign discount codes to multiple users
CREATE TABLE discount_user (
    id SERIAL PRIMARY KEY,
    discount_code_id INTEGER NOT NULL REFERENCES discount_codes(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
    status driver_application_status_enum,
    admin_id INTEGER REFERENCES admins(user_id),
    review_date TIMESTAMP,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- File storage table
CREATE TABLE files (
    id SERIAL PRIMARY KEY,
    file_path VARCHAR(255) NOT NULL,
    file_name VARCHAR(255),
    file_size INTEGER,
    mime_type VARCHAR(100),
    uploaded_by INTEGER REFERENCES users(id),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Updated documents table, now referencing files table
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    type document_type_enum,
    file_id INTEGER REFERENCES files(id) NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status document_status_enum,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Transactions Table (for wallet & system financial operations)
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    amount NUMERIC(15,2) NOT NULL,
    type transaction_type_enum,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_id INTEGER REFERENCES payments(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Indexes for performance (example)
CREATE INDEX idx_trips_start_location ON trips USING GIST(start_location);
CREATE INDEX idx_trips_end_location ON trips USING GIST(end_location);
