#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script
Migrates all data from database.db to Supabase PostgreSQL
"""

import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}⚠ {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    print(f"{BLUE}ℹ {message}{RESET}")

def connect_sqlite():
    """Connect to SQLite database"""
    if not os.path.exists('database.db'):
        print_error("database.db not found!")
        return None
    
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def connect_postgres():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('SUPABASE_HOST'),
            database=os.getenv('SUPABASE_DB'),
            user=os.getenv('SUPABASE_USER'),
            password=os.getenv('SUPABASE_PASSWORD'),
            port=os.getenv('SUPABASE_PORT', 6543)
        )
        return conn
    except Exception as e:
        print_error(f"PostgreSQL connection failed: {e}")
        return None

def migrate_admin_users(sqlite_conn, pg_conn):
    """Migrate admin users"""
    print_info("Migrating admin users...")
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # Get SQLite data
    sqlite_cursor.execute("SELECT * FROM admin_users")
    users = sqlite_cursor.fetchall()
    
    migrated = 0
    skipped = 0
    
    for user in users:
        try:
            pg_cursor.execute("""
                INSERT INTO admin_users 
                (user_id, password_hash, full_name, created_at, last_login)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
            """, (
                user['user_id'],
                user['password_hash'],
                user['full_name'],
                user['created_at'],
                user['last_login']
            ))
            
            if pg_cursor.rowcount > 0:
                migrated += 1
            else:
                skipped += 1
                
        except Exception as e:
            print_warning(f"Failed to migrate user {user['user_id']}: {e}")
            skipped += 1
    
    pg_conn.commit()
    print_success(f"Admin users: {migrated} migrated, {skipped} skipped")
    return migrated

def migrate_vehicles(sqlite_conn, pg_conn):
    """Migrate vehicles"""
    print_info("Migrating vehicles...")
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # Get SQLite data
    sqlite_cursor.execute("SELECT * FROM vehicles")
    vehicles = sqlite_cursor.fetchall()
    
    migrated = 0
    skipped = 0
    
    for vehicle in vehicles:
        try:
            pg_cursor.execute("""
                INSERT INTO vehicles 
                (name, type, cc, license_plate, category, 
                 price_day, price_3day, price_weekly, price_monthly,
                 image_url, terms_and_conditions, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    type = EXCLUDED.type,
                    cc = EXCLUDED.cc,
                    license_plate = EXCLUDED.license_plate,
                    category = EXCLUDED.category,
                    price_day = EXCLUDED.price_day,
                    price_3day = EXCLUDED.price_3day,
                    price_weekly = EXCLUDED.price_weekly,
                    price_monthly = EXCLUDED.price_monthly,
                    image_url = EXCLUDED.image_url,
                    terms_and_conditions = EXCLUDED.terms_and_conditions,
                    is_active = EXCLUDED.is_active
                RETURNING id
            """, (
                vehicle['name'],
                vehicle['type'],
                vehicle['cc'],
                vehicle['license_plate'],
                vehicle.get('category', 'Motor'),
                vehicle['price_day'],
                vehicle['price_3day'],
                vehicle['price_weekly'],
                vehicle['price_monthly'],
                vehicle['image_url'],
                vehicle.get('terms_and_conditions'),
                vehicle['is_active'],
                vehicle['created_at']
            ))
            
            migrated += 1
                
        except Exception as e:
            print_warning(f"Failed to migrate vehicle {vehicle['name']}: {e}")
            skipped += 1
    
    pg_conn.commit()
    print_success(f"Vehicles: {migrated} migrated, {skipped} skipped")
    return migrated

def migrate_bookings(sqlite_conn, pg_conn):
    """Migrate bookings"""
    print_info("Migrating bookings...")
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # Get SQLite data
    sqlite_cursor.execute("SELECT * FROM bookings")
    bookings = sqlite_cursor.fetchall()
    
    migrated = 0
    skipped = 0
    
    for booking in bookings:
        try:
            # Get PostgreSQL vehicle_id from name
            sqlite_cursor.execute("SELECT name FROM vehicles WHERE id = ?", (booking['vehicle_id'],))
            vehicle = sqlite_cursor.fetchone()
            
            if not vehicle:
                print_warning(f"Vehicle not found for booking {booking.get('booking_number', booking['id'])}")
                skipped += 1
                continue
            
            pg_cursor.execute("SELECT id FROM vehicles WHERE name = %s", (vehicle['name'],))
            pg_vehicle = pg_cursor.fetchone()
            
            if not pg_vehicle:
                print_warning(f"Vehicle {vehicle['name']} not found in PostgreSQL")
                skipped += 1
                continue
            
            pg_vehicle_id = pg_vehicle[0]
            
            pg_cursor.execute("""
                INSERT INTO bookings 
                (booking_number, vehicle_id, customer_name, ic_number, 
                 nationality, customer_photo, location, destination,
                 start_date, pickup_time, end_date, return_time,
                 total_price, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (booking_number) DO NOTHING
            """, (
                booking.get('booking_number', f"VR-MIGRATED-{booking['id']}"),
                pg_vehicle_id,
                booking['customer_name'],
                booking.get('ic_number'),
                booking.get('nationality', 'Malaysian'),
                booking.get('customer_photo'),
                booking.get('location'),
                booking.get('destination'),
                booking['start_date'],
                booking['pickup_time'],
                booking['end_date'],
                booking['return_time'],
                booking.get('total_price'),
                booking['status'],
                booking.get('created_at')
            ))
            
            if pg_cursor.rowcount > 0:
                migrated += 1
            else:
                skipped += 1
                
        except Exception as e:
            print_warning(f"Failed to migrate booking {booking.get('id')}: {e}")
            skipped += 1
    
    pg_conn.commit()
    print_success(f"Bookings: {migrated} migrated, {skipped} skipped")
    return migrated

def verify_migration(pg_conn):
    """Verify migration results"""
    print_info("Verifying migration...")
    
    cursor = pg_conn.cursor(cursor_factory=RealDictCursor)
    
    # Count records
    cursor.execute("SELECT COUNT(*) as count FROM admin_users")
    admin_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM vehicles")
    vehicle_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM bookings")
    booking_count = cursor.fetchone()['count']
    
    print()
    print("=" * 60)
    print(f"  MIGRATION VERIFICATION")
    print("=" * 60)
    print(f"  Admin Users: {admin_count}")
    print(f"  Vehicles:    {vehicle_count}")
    print(f"  Bookings:    {booking_count}")
    print("=" * 60)
    print()

def main():
    """Main migration function"""
    print()
    print("=" * 60)
    print("  VehiclesRent - SQLite to PostgreSQL Migration")
    print("=" * 60)
    print()
    
    # Check .env file
    if not os.path.exists('.env'):
        print_error(".env file not found!")
        print_info("Please create .env file with Supabase credentials")
        return
    
    # Connect to databases
    print_info("Connecting to databases...")
    
    sqlite_conn = connect_sqlite()
    if not sqlite_conn:
        return
    print_success("Connected to SQLite")
    
    pg_conn = connect_postgres()
    if not pg_conn:
        sqlite_conn.close()
        return
    print_success("Connected to PostgreSQL")
    print()
    
    try:
        # Run migrations
        total_migrated = 0
        
        total_migrated += migrate_admin_users(sqlite_conn, pg_conn)
        total_migrated += migrate_vehicles(sqlite_conn, pg_conn)
        total_migrated += migrate_bookings(sqlite_conn, pg_conn)
        
        print()
        
        # Verify
        verify_migration(pg_conn)
        
        # Summary
        print_success(f"Migration completed! Total records migrated: {total_migrated}")
        print()
        print_info("Next steps:")
        print("  1. Test login: admin / admin123")
        print("  2. Verify all data in Supabase dashboard")
        print("  3. Update app to use app_postgresql.py")
        print("  4. Deploy to production")
        print()
        
    except Exception as e:
        print_error(f"Migration failed: {e}")
        pg_conn.rollback()
        
    finally:
        sqlite_conn.close()
        pg_conn.close()
        print_info("Database connections closed")

if __name__ == '__main__':
    main()