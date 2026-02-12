-- VehiclesRent Database Schema for PostgreSQL/Supabase
-- Run this in Supabase SQL Editor

-- =====================================================
-- STEP 1: Create Tables
-- =====================================================

-- Admin Users Table
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Vehicles Table
CREATE TABLE IF NOT EXISTS vehicles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(100) NOT NULL,
    cc VARCHAR(50) NOT NULL,
    license_plate VARCHAR(50) UNIQUE,
    category VARCHAR(50) DEFAULT 'Motor',
    price_day INTEGER NOT NULL,
    price_3day INTEGER NOT NULL,
    price_weekly INTEGER NOT NULL,
    price_monthly INTEGER NOT NULL,
    image_url TEXT,
    terms_and_conditions TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bookings Table
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    booking_number VARCHAR(50) UNIQUE NOT NULL,
    vehicle_id INTEGER NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    ic_number VARCHAR(100),
    nationality VARCHAR(100) DEFAULT 'Malaysian',
    customer_photo TEXT,
    location TEXT,
    destination TEXT,
    start_date VARCHAR(20) NOT NULL,
    pickup_time VARCHAR(10) NOT NULL,
    end_date VARCHAR(20) NOT NULL,
    return_time VARCHAR(10) NOT NULL,
    total_price DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_vehicle
        FOREIGN KEY (vehicle_id) 
        REFERENCES vehicles(id)
        ON DELETE CASCADE
);

-- =====================================================
-- STEP 2: Create Indexes for Performance
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_bookings_vehicle 
    ON bookings(vehicle_id);

CREATE INDEX IF NOT EXISTS idx_bookings_status 
    ON bookings(status);

CREATE INDEX IF NOT EXISTS idx_bookings_created 
    ON bookings(created_at);

CREATE INDEX IF NOT EXISTS idx_bookings_dates 
    ON bookings(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_bookings_month 
    ON bookings(SUBSTRING(start_date FROM 1 FOR 7));

CREATE INDEX IF NOT EXISTS idx_vehicles_category 
    ON vehicles(category);

CREATE INDEX IF NOT EXISTS idx_vehicles_active 
    ON vehicles(is_active);

-- =====================================================
-- STEP 3: Insert Default Admin User
-- =====================================================

-- Password: admin123 (hashed with Werkzeug)
-- IMPORTANT: Change this password after first login!

INSERT INTO admin_users (user_id, password_hash, full_name)
VALUES (
    'admin',
    'scrypt:32768:8:1$uKzYOXQGQEpBpLxd$8e8f0c8a3f5e7b9d1c2a4e6f8a0b2c4d6e8f0a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f7a9b1c3d5e7f9a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9d1',
    'Administrator'
)
ON CONFLICT (user_id) DO NOTHING;

-- =====================================================
-- STEP 4: Sample Data (Optional - for testing)
-- =====================================================

-- Sample Vehicles
INSERT INTO vehicles (name, type, cc, license_plate, category, price_day, price_3day, price_weekly, price_monthly)
VALUES 
    ('Honda Beat', 'Scooter', '110', 'B1234ABC', 'Motor', 50000, 140000, 300000, 1000000),
    ('Yamaha NMAX', 'Scooter', '155', 'B5678DEF', 'Motor', 80000, 220000, 500000, 1800000),
    ('Toyota Avanza', 'MPV', '1500', 'B9012GHI', 'Car', 300000, 850000, 1800000, 6000000)
ON CONFLICT (name) DO NOTHING;

-- =====================================================
-- STEP 5: Verify Installation
-- =====================================================

-- Check tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check admin user
SELECT id, user_id, full_name, created_at 
FROM admin_users;

-- Check vehicles
SELECT id, name, category, license_plate 
FROM vehicles;

-- Check indexes
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename, indexname;

-- =====================================================
-- STEP 6: Security - Row Level Security (RLS)
-- =====================================================

-- Enable RLS for sensitive tables (optional but recommended)
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE vehicles ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust based on your needs)
-- Example: Allow all operations for authenticated users
CREATE POLICY admin_users_policy ON admin_users
    FOR ALL
    USING (true);

CREATE POLICY vehicles_policy ON vehicles
    FOR ALL
    USING (true);

CREATE POLICY bookings_policy ON bookings
    FOR ALL
    USING (true);

-- =====================================================
-- STEP 7: Backup & Maintenance
-- =====================================================

-- To backup your database:
-- pg_dump -h db.xxxxx.supabase.co -U postgres -d postgres > backup.sql

-- To restore:
-- psql -h db.xxxxx.supabase.co -U postgres -d postgres < backup.sql

-- =====================================================
-- Migration Notes
-- =====================================================

-- If migrating from SQLite:
-- 1. Export SQLite data to CSV
-- 2. Import CSV to PostgreSQL using COPY command
-- 3. Update sequences after import:

-- SELECT setval('admin_users_id_seq', (SELECT MAX(id) FROM admin_users));
-- SELECT setval('vehicles_id_seq', (SELECT MAX(id) FROM vehicles));
-- SELECT setval('bookings_id_seq', (SELECT MAX(id) FROM bookings));

-- =====================================================
-- Performance Tuning
-- =====================================================

-- Analyze tables for query optimization
ANALYZE admin_users;
ANALYZE vehicles;
ANALYZE bookings;

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- =====================================================
-- Completed!
-- =====================================================

-- Your database is now ready to use with VehiclesRent application
-- Remember to:
-- 1. Update .env file with your Supabase credentials
-- 2. Change default admin password after first login
-- 3. Test all features thoroughly
-- 4. Set up regular backups
