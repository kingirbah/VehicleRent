#!/usr/bin/env python3
"""
Enhanced Migration Script: SQLite to PostgreSQL
Migrate VehicleRent data from SQLite to PostgreSQL/Supabase
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
import sys
from urllib.parse import urlparse

def get_postgres_config():
    """Get PostgreSQL configuration from environment"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Parse DATABASE_URL
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        result = urlparse(database_url)
        return {
            'host': result.hostname,
            'database': result.path[1:],
            'user': result.username,
            'password': result.password,
            'port': result.port or 5432
        }
    else:
        # Use individual environment variables
        return {
            'host': os.environ.get('SUPABASE_HOST'),
            'database': os.environ.get('SUPABASE_DB', 'postgres'),
            'user': os.environ.get('SUPABASE_USER'),
            'password': os.environ.get('SUPABASE_PASSWORD'),
            'port': os.environ.get('SUPABASE_PORT', 5432)
        }

def migrate_data(sqlite_db_path):
    """
    Migrate all data from SQLite to PostgreSQL
    
    Args:
        sqlite_db_path: Path to SQLite database file
    """
    
    print("=" * 70)
    print("🔄 VehicleRent Database Migration - SQLite → PostgreSQL")
    print("=" * 70)
    
    # Get PostgreSQL configuration
    print("\n🔧 Getting database configuration...")
    pg_config = get_postgres_config()
    
    if not pg_config['host'] or not pg_config['password']:
        print("❌ Error: Database configuration incomplete!")
        print("\nPlease set one of:")
        print("  1. DATABASE_URL environment variable")
        print("     export DATABASE_URL='postgresql://user:pass@host:5432/db'")
        print("\n  2. Individual environment variables:")
        print("     export SUPABASE_HOST='db.xxx.supabase.co'")
        print("     export SUPABASE_USER='postgres.xxx'")
        print("     export SUPABASE_PASSWORD='your_password'")
        sys.exit(1)
    
    print(f"   ✅ Host: {pg_config['host']}")
    print(f"   ✅ Database: {pg_config['database']}")
    print(f"   ✅ User: {pg_config['user']}")
    
    # Connect to SQLite
    print("\n📂 Connecting to SQLite database...")
    try:
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cur = sqlite_conn.cursor()
        print("   ✅ SQLite connected")
    except Exception as e:
        print(f"   ❌ Error connecting to SQLite: {e}")
        sys.exit(1)
    
    # Connect to PostgreSQL
    print("\n🐘 Connecting to PostgreSQL database...")
    try:
        pg_conn = psycopg2.connect(**pg_config)
        pg_cur = pg_conn.cursor()
        print("   ✅ PostgreSQL connected")
    except Exception as e:
        print(f"   ❌ Error connecting to PostgreSQL: {e}")
        print("\nTroubleshooting:")
        print("  - Check your database credentials")
        print("  - Verify the database is running")
        print("  - Check firewall/security settings")
        sys.exit(1)
    
    try:
        # Create tables if they don't exist
        print("\n🔨 Creating tables...")
        
        # Admin users table
        pg_cur.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        print("   ✅ admin_users table ready")
        
        # Vehicles table
        pg_cur.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                type VARCHAR(100) NOT NULL,
                cc VARCHAR(50) NOT NULL,
                license_plate VARCHAR(50) UNIQUE,
                category VARCHAR(100) DEFAULT 'Motor',
                price_day INTEGER NOT NULL,
                price_3day INTEGER NOT NULL,
                price_weekly INTEGER NOT NULL,
                price_monthly INTEGER NOT NULL,
                image_url TEXT,
                terms_and_conditions TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("   ✅ vehicles table ready")
        
        # Bookings table
        pg_cur.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id SERIAL PRIMARY KEY,
                booking_number VARCHAR(50) UNIQUE NOT NULL,
                vehicle_id INTEGER NOT NULL,
                customer_name VARCHAR(255) NOT NULL,
                ic_number VARCHAR(100),
                nationality VARCHAR(100) DEFAULT 'Malaysian',
                customer_photo TEXT,
                location VARCHAR(255),
                destination VARCHAR(255),
                start_date VARCHAR(50) NOT NULL,
                pickup_time VARCHAR(50) NOT NULL,
                end_date VARCHAR(50) NOT NULL,
                return_time VARCHAR(50) NOT NULL,
                total_price DECIMAL(10,2),
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE
            )
        ''')
        print("   ✅ bookings table ready")
        
        pg_conn.commit()
        
        # Migrate admin_users
        print("\n👥 Migrating admin_users...")
        sqlite_cur.execute("SELECT * FROM admin_users")
        admin_users = sqlite_cur.fetchall()
        
        if admin_users:
            pg_cur.execute("DELETE FROM admin_users")
            
            for user in admin_users:
                pg_cur.execute("""
                    INSERT INTO admin_users (user_id, password_hash, full_name, created_at, last_login)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    user['user_id'],
                    user['password_hash'],
                    user['full_name'],
                    user['created_at'],
                    user['last_login']
                ))
            
            pg_conn.commit()
            print(f"   ✅ Migrated {len(admin_users)} admin users")
        else:
            print("   ⚠️  No admin users found")
        
        # Migrate vehicles
        print("\n🚗 Migrating vehicles...")
        sqlite_cur.execute("SELECT * FROM vehicles")
        vehicles = sqlite_cur.fetchall()
        
        if vehicles:
            pg_cur.execute("DELETE FROM vehicles")
            
            for vehicle in vehicles:
                pg_cur.execute("""
                    INSERT INTO vehicles (
                        name, type, cc, license_plate, category,
                        price_day, price_3day, price_weekly, price_monthly,
                        image_url, terms_and_conditions, is_active, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    vehicle['name'],
                    vehicle['type'],
                    vehicle['cc'],
                    vehicle['license_plate'],
                    vehicle['category'],
                    vehicle['price_day'],
                    vehicle['price_3day'],
                    vehicle['price_weekly'],
                    vehicle['price_monthly'],
                    vehicle['image_url'],
                    vehicle['terms_and_conditions'],
                    vehicle['is_active'],
                    vehicle['created_at']
                ))
            
            pg_conn.commit()
            print(f"   ✅ Migrated {len(vehicles)} vehicles")
        else:
            print("   ⚠️  No vehicles found")
        
        # Migrate bookings
        print("\n📅 Migrating bookings...")
        sqlite_cur.execute("SELECT * FROM bookings")
        bookings = sqlite_cur.fetchall()
        
        if bookings:
            pg_cur.execute("DELETE FROM bookings")
            
            for booking in bookings:
                pg_cur.execute("""
                    INSERT INTO bookings (
                        booking_number, vehicle_id, customer_name, ic_number,
                        nationality, customer_photo, location, destination,
                        start_date, pickup_time, end_date, return_time,
                        total_price, status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    booking['booking_number'],
                    booking['vehicle_id'],
                    booking['customer_name'],
                    booking['ic_number'],
                    booking['nationality'],
                    booking['customer_photo'],
                    booking['location'],
                    booking['destination'],
                    booking['start_date'],
                    booking['pickup_time'],
                    booking['end_date'],
                    booking['return_time'],
                    booking['total_price'],
                    booking['status'],
                    booking['created_at']
                ))
            
            pg_conn.commit()
            print(f"   ✅ Migrated {len(bookings)} bookings")
        else:
            print("   ⚠️  No bookings found")
        
        # Verify migration
        print("\n🔍 Verifying migration...")
        
        pg_cur.execute("SELECT COUNT(*) FROM admin_users")
        pg_users = pg_cur.fetchone()[0]
        
        pg_cur.execute("SELECT COUNT(*) FROM vehicles")
        pg_vehicles = pg_cur.fetchone()[0]
        
        pg_cur.execute("SELECT COUNT(*) FROM bookings")
        pg_bookings = pg_cur.fetchone()[0]
        
        print(f"\n📊 Migration Results:")
        print(f"   SQLite     → Users: {len(admin_users)}, Vehicles: {len(vehicles)}, Bookings: {len(bookings)}")
        print(f"   PostgreSQL → Users: {pg_users}, Vehicles: {pg_vehicles}, Bookings: {pg_bookings}")
        
        if pg_users == len(admin_users) and pg_vehicles == len(vehicles) and pg_bookings == len(bookings):
            print("\n   ✅ Migration verified successfully!")
        else:
            print("\n   ⚠️  Warning: Count mismatch detected")
        
    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        pg_conn.rollback()
        raise
    
    finally:
        sqlite_cur.close()
        sqlite_conn.close()
        pg_cur.close()
        pg_conn.close()
    
    print("\n" + "=" * 70)
    print("✅ Migration completed successfully!")
    print("=" * 70)
    print("\n📋 Next steps:")
    print("   1. ✅ Data migrated to PostgreSQL")
    print("   2. Set environment variables in Koyeb dashboard")
    print("   3. Redeploy your application")
    print("   4. Test login and all features")
    print("\n🎉 You're ready to go!\n")


if __name__ == "__main__":
    # Configuration
    SQLITE_DB = "database.db"
    
    # Check if SQLite database exists
    if not os.path.exists(SQLITE_DB):
        print(f"❌ Error: SQLite database not found: {SQLITE_DB}")
        print("\nPlease ensure database.db is in the current directory.")
        sys.exit(1)
    
    # Run migration
    migrate_data(SQLITE_DB)
