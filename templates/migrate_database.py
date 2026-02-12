#!/usr/bin/env python3
"""
Comprehensive Database Migration Script
Adds all new features to existing JomSewa database
"""

import sqlite3
import os
from datetime import datetime
import shutil

def backup_database():
    """Create backup before migration"""
    if os.path.exists('database.db'):
        backup_name = f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2('database.db', backup_name)
        print(f"✓ Backup created: {backup_name}")
        return backup_name
    return None

def migrate_database():
    """Run all migrations"""
    print("\n" + "="*70)
    print("  JOMSEWA DATABASE MIGRATION - V6.0")
    print("="*70 + "\n")
    
    # Backup first
    print("📦 Creating backup...")
    backup_file = backup_database()
    if backup_file:
        print(f"   Backup saved as: {backup_file}\n")
    else:
        print("   No existing database found - will create new one\n")
    
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Migration 1: Add license_plate to vehicles
        print("🚗 Migration 1: Adding license_plate to vehicles...")
        cursor.execute("PRAGMA table_info(vehicles)")
        vehicle_columns = [column[1] for column in cursor.fetchall()]
        
        if 'license_plate' not in vehicle_columns:
            conn.execute("ALTER TABLE vehicles ADD COLUMN license_plate TEXT UNIQUE")
            print("   ✓ license_plate column added")
        else:
            print("   ⊙ license_plate column already exists")
        
        # Migration 2: Add booking_number to bookings
        print("\n📋 Migration 2: Adding booking_number to bookings...")
        cursor.execute("PRAGMA table_info(bookings)")
        booking_columns = [column[1] for column in cursor.fetchall()]
        
        if 'booking_number' not in booking_columns:
            conn.execute("ALTER TABLE bookings ADD COLUMN booking_number TEXT")
            print("   ✓ booking_number column added")
            
            # Generate booking numbers for existing records
            cursor.execute("SELECT id, created_at FROM bookings WHERE booking_number IS NULL OR booking_number = ''")
            existing_bookings = cursor.fetchall()
            
            if existing_bookings:
                print(f"   🔢 Generating booking numbers for {len(existing_bookings)} records...")
                date_counters = {}
                
                for booking in existing_bookings:
                    booking_id = booking[0]
                    created_at = booking[1] or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    date_str = created_at.split(' ')[0].replace('-', '')
                    
                    if date_str not in date_counters:
                        date_counters[date_str] = 0
                    
                    date_counters[date_str] += 1
                    sequence = str(date_counters[date_str]).zfill(4)
                    booking_number = f'JS-{date_str}-{sequence}'
                    
                    conn.execute("UPDATE bookings SET booking_number = ? WHERE id = ?", 
                               (booking_number, booking_id))
                    
                    if booking_id % 10 == 0:  # Progress indicator
                        print(f"      {booking_id}/{len(existing_bookings)} bookings processed...")
                
                print(f"   ✓ Generated {len(existing_bookings)} booking numbers")
        else:
            print("   ⊙ booking_number column already exists")
            
            # Check for missing booking numbers
            cursor.execute("SELECT COUNT(*) FROM bookings WHERE booking_number IS NULL OR booking_number = ''")
            missing = cursor.fetchone()[0]
            
            if missing > 0:
                print(f"   ⚠ Found {missing} bookings without booking numbers - generating...")
                cursor.execute("SELECT id, created_at FROM bookings WHERE booking_number IS NULL OR booking_number = ''")
                existing_bookings = cursor.fetchall()
                
                date_counters = {}
                for booking in existing_bookings:
                    booking_id = booking[0]
                    created_at = booking[1] or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    date_str = created_at.split(' ')[0].replace('-', '')
                    
                    if date_str not in date_counters:
                        date_counters[date_str] = 0
                    
                    date_counters[date_str] += 1
                    sequence = str(date_counters[date_str]).zfill(4)
                    booking_number = f'JS-{date_str}-{sequence}'
                    
                    conn.execute("UPDATE bookings SET booking_number = ? WHERE id = ?", 
                               (booking_number, booking_id))
                
                print(f"   ✓ Fixed {missing} bookings")
        
        # Migration 3: Add nationality to bookings
        print("\n🌍 Migration 3: Adding nationality to bookings...")
        if 'nationality' not in booking_columns:
            conn.execute("ALTER TABLE bookings ADD COLUMN nationality TEXT DEFAULT 'Malaysian'")
            print("   ✓ nationality column added")
            
            # Update existing records
            conn.execute("UPDATE bookings SET nationality = 'Malaysian' WHERE nationality IS NULL")
            updated = cursor.rowcount
            if updated > 0:
                print(f"   ✓ Updated {updated} existing records with default nationality")
        else:
            print("   ⊙ nationality column already exists")
        
        # Migration 4: Create indexes for performance
        print("\n⚡ Migration 4: Creating performance indexes...")
        indexes = [
            ("idx_bookings_vehicle", "CREATE INDEX IF NOT EXISTS idx_bookings_vehicle ON bookings(vehicle_id)"),
            ("idx_bookings_status", "CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status)"),
            ("idx_bookings_created", "CREATE INDEX IF NOT EXISTS idx_bookings_created ON bookings(created_at)"),
            ("idx_bookings_dates", "CREATE INDEX IF NOT EXISTS idx_bookings_dates ON bookings(start_date, end_date)"),
        ]
        
        for idx_name, idx_sql in indexes:
            try:
                conn.execute(idx_sql)
                print(f"   ✓ Created index: {idx_name}")
            except sqlite3.OperationalError:
                print(f"   ⊙ Index already exists: {idx_name}")
        
        # Commit all changes
        conn.commit()
        
        # Verification
        print("\n" + "="*70)
        print("  VERIFICATION")
        print("="*70)
        
        # Check vehicles
        cursor.execute("PRAGMA table_info(vehicles)")
        vehicle_cols = [column[1] for column in cursor.fetchall()]
        print(f"\n📋 Vehicles table columns: {len(vehicle_cols)}")
        for col in vehicle_cols:
            print(f"   • {col}")
        
        # Check bookings
        cursor.execute("PRAGMA table_info(bookings)")
        booking_cols = [column[1] for column in cursor.fetchall()]
        print(f"\n📋 Bookings table columns: {len(booking_cols)}")
        for col in booking_cols:
            print(f"   • {col}")
        
        # Stats
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        vehicle_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bookings")
        booking_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bookings WHERE booking_number IS NOT NULL AND booking_number != ''")
        booking_with_numbers = cursor.fetchone()[0]
        
        print(f"\n📊 Statistics:")
        print(f"   Total vehicles: {vehicle_count}")
        print(f"   Total bookings: {booking_count}")
        print(f"   Bookings with booking numbers: {booking_with_numbers}")
        
        if booking_count == booking_with_numbers:
            print("   ✓ All bookings have booking numbers!")
        else:
            print(f"   ⚠ {booking_count - booking_with_numbers} bookings missing booking numbers")
        
        # Sample data
        if vehicle_count > 0:
            print("\n📄 Sample Vehicles:")
            cursor.execute("SELECT id, name, type, license_plate FROM vehicles LIMIT 3")
            for row in cursor.fetchall():
                plate = row[3] or 'No plate'
                print(f"   {row[0]}. {row[1]} ({row[2]}) - Plate: {plate}")
        
        if booking_count > 0:
            print("\n📄 Sample Bookings:")
            cursor.execute("SELECT id, booking_number, customer_name, nationality FROM bookings LIMIT 3")
            for row in cursor.fetchall():
                print(f"   {row[0]}. {row[1]} - {row[2]} ({row[3]})")
        
        print("\n" + "="*70)
        print("  ✓ MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*70)
        
        print(f"\n💡 Tips:")
        print(f"   • Backup saved as: {backup_file}")
        print(f"   • You can safely delete backup after verifying everything works")
        print(f"   • Run 'python app.py' to start the application")
        print(f"   • Access admin panel at http://localhost:5000/login")
        
    except Exception as e:
        print(f"\n❌ ERROR during migration: {e}")
        print(f"\n🔄 Rolling back changes...")
        conn.rollback()
        
        if backup_file and os.path.exists(backup_file):
            print(f"   Restore from backup: cp {backup_file} database.db")
        
        raise
    
    finally:
        conn.close()


if __name__ == '__main__':
    print("\n⚠️  WARNING: This script will modify your database!")
    print("   A backup will be created automatically.")
    print("   Make sure the application is not running.\n")
    
    response = input("Continue with migration? (yes/no): ").lower().strip()
    
    if response == 'yes':
        migrate_database()
    else:
        print("\n❌ Migration cancelled by user.")
        print("   No changes were made to the database.\n")
