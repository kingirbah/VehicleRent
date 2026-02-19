from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import io
from PIL import Image
from dotenv import load_dotenv
from contextlib import contextmanager
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'vehiclesrent_v7_ultra_secure_key_2026_production')

# --- CONFIGURATION ---
WHATSAPP_NUMBER = os.getenv('WHATSAPP_NUMBER', '6285111040408')

# Database configuration - FIXED to prevent local socket connection
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    # Fix postgres:// to postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    # Parse DATABASE_URL
    result = urlparse(DATABASE_URL)
    DB_CONFIG = {
        'host': result.hostname,
        'database': result.path[1:] if result.path else 'postgres',  # Remove leading /
        'user': result.username,
        'password': result.password,
        'port': result.port or 6543
    }
    print(f"📊 Using DATABASE_URL: {result.hostname}")
else:
    # Fallback to individual environment variables
    DB_CONFIG = {
        'host': os.getenv('SUPABASE_HOST'),
        'database': os.getenv('SUPABASE_DB', 'postgres'),
        'user': os.getenv('SUPABASE_USER', 'postgres'),
        'password': os.getenv('SUPABASE_PASSWORD'),
        'port': int(os.getenv('SUPABASE_PORT', '6543'))
    }
    print(f"📊 Using individual env vars: {DB_CONFIG.get('host', 'NOT SET')}")

# CRITICAL FIX: Remove None values to prevent psycopg2 local socket fallback
DB_CONFIG = {k: v for k, v in DB_CONFIG.items() if v is not None}

# Validate database configuration
if not DB_CONFIG.get('host') or not DB_CONFIG.get('password'):
    print("\n" + "="*70)
    print("⚠️  WARNING: Database configuration incomplete!")
    print("="*70)
    print("\nMissing required environment variables:")
    if not DB_CONFIG.get('host'):
        print("  ❌ Database host not set")
    if not DB_CONFIG.get('password'):
        print("  ❌ Database password not set")
    print("\nPlease set ONE of these in Koyeb Environment Variables:")
    print("  1. DATABASE_URL (recommended)")
    print("     DATABASE_URL=postgresql://user:pass@host:5432/db")
    print("\n  2. Individual variables:")
    print("     SUPABASE_HOST=db.xxx.supabase.co")
    print("     SUPABASE_USER=postgres.xxx")
    print("     SUPABASE_PASSWORD=your_password")
    print("     SUPABASE_DB=postgres")
    print("     SUPABASE_PORT=6543")
    print("="*70 + "\n")

# Upload configuration
UPLOAD_FOLDER = 'static/uploads/vehicles'
CUSTOMER_PHOTO_FOLDER = 'static/uploads/customers'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB

# Pagination
ITEMS_PER_PAGE = 50

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CUSTOMER_PHOTO_FOLDER, exist_ok=True)


# --- DATABASE CONNECTION ---
@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        # Ensure we have required config before attempting connection
        if not DB_CONFIG.get('host'):
            raise ValueError("Database host not configured. Please set DATABASE_URL or SUPABASE_HOST")
        
        conn = psycopg2.connect(**DB_CONFIG)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"❌ Database error: {e}")
            raise e
    except psycopg2.OperationalError as e:
        print(f"\n❌ Database connection failed!")
        print(f"Error: {e}")
        print(f"\nCurrent config:")
        print(f"  Host: {DB_CONFIG.get('host', 'NOT SET')}")
        print(f"  Database: {DB_CONFIG.get('database', 'NOT SET')}")
        print(f"  User: {DB_CONFIG.get('user', 'NOT SET')}")
        print(f"  Port: {DB_CONFIG.get('port', 'NOT SET')}")
        print(f"\nPlease verify your environment variables in Koyeb!")
        raise
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def get_db_cursor(conn):
    """Get cursor with RealDictCursor for dict-like rows"""
    return conn.cursor(cursor_factory=RealDictCursor)


# --- FILE UPLOAD HELPERS ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def compress_and_save_image(file, filename, folder=UPLOAD_FOLDER):
    """Compress image to ensure it's under 1MB and save it"""
    try:
        img = Image.open(file)
        
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        quality = 90
        while quality > 20:
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            size = buffer.tell()
            
            if size <= MAX_FILE_SIZE:
                filepath = os.path.join(folder, filename)
                with open(filepath, 'wb') as f:
                    f.write(buffer.getvalue())
                return filepath
            
            quality -= 10
        
        img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        
        filepath = os.path.join(folder, filename)
        with open(filepath, 'wb') as f:
            f.write(buffer.getvalue())
        
        return filepath
        
    except Exception as e:
        print(f"Error compressing image: {e}")
        return None


# --- DATABASE INITIALIZATION ---
def init_db():
    """Check and update database schema"""
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        
        print("\nChecking database schema...")
        
        # Check vehicles table columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'vehicles'
        """)
        vehicle_columns = [row['column_name'] for row in cursor.fetchall()]
        
        # Add missing columns to vehicles if needed
        if 'license_plate' not in vehicle_columns:
            cursor.execute("ALTER TABLE vehicles ADD COLUMN license_plate VARCHAR(50) UNIQUE")
            print("  ✅ Added column: license_plate")
        
        if 'category' not in vehicle_columns:
            cursor.execute("ALTER TABLE vehicles ADD COLUMN category VARCHAR(50) DEFAULT 'Motor'")
            cursor.execute("UPDATE vehicles SET category = 'Motor' WHERE category IS NULL")
            print("  ✅ Added column: category")
        
        if 'terms_and_conditions' not in vehicle_columns:
            cursor.execute("ALTER TABLE vehicles ADD COLUMN terms_and_conditions TEXT")
            print("  ✅ Added column: terms_and_conditions")
        
        # Check bookings table columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bookings'
        """)
        booking_columns = [row['column_name'] for row in cursor.fetchall()]
        
        if 'booking_number' not in booking_columns:
            cursor.execute("ALTER TABLE bookings ADD COLUMN booking_number VARCHAR(50) UNIQUE")
            print("  ✅ Added column: booking_number")
            
            # Generate booking numbers for existing records
            cursor.execute("SELECT id, created_at FROM bookings WHERE booking_number IS NULL OR booking_number = ''")
            existing_bookings = cursor.fetchall()
            
            if existing_bookings:
                date_counters = {}
                for booking in existing_bookings:
                    booking_id = booking['id']
                    created_at = booking['created_at'] or datetime.now()
                    date_str = created_at.strftime('%Y%m%d')
                    
                    if date_str not in date_counters:
                        date_counters[date_str] = 0
                    
                    date_counters[date_str] += 1
                    sequence = str(date_counters[date_str]).zfill(4)
                    booking_number = f'VR-{date_str}-{sequence}'
                    
                    cursor.execute("UPDATE bookings SET booking_number = %s WHERE id = %s", 
                                 (booking_number, booking_id))
                print(f"  ✅ Generated {len(existing_bookings)} booking numbers")
        
        if 'nationality' not in booking_columns:
            cursor.execute("ALTER TABLE bookings ADD COLUMN nationality VARCHAR(100) DEFAULT 'Malaysian'")
            print("  ✅ Added column: nationality")
        
        if 'customer_photo' not in booking_columns:
            cursor.execute("ALTER TABLE bookings ADD COLUMN customer_photo TEXT")
            print("  ✅ Added column: customer_photo")
        
        if 'total_price' not in booking_columns:
            cursor.execute("ALTER TABLE bookings ADD COLUMN total_price DECIMAL(10,2)")
            print("  ✅ Added column: total_price")
        
        # Check if default admin exists
        cursor.execute("SELECT COUNT(*) as count FROM admin_users")
        admin_count = cursor.fetchone()['count']
        
        if admin_count == 0:
            default_hash = generate_password_hash('admin123')
            cursor.execute(
                "INSERT INTO admin_users (user_id, password_hash, full_name) VALUES (%s, %s, %s)",
                ('admin', default_hash, 'Administrator')
            )
            print("  ✅ Default admin created - user_id: admin, password: admin123")
        
        conn.commit()
        print("Database schema check completed!\n")


# --- AUTHENTICATION ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please login to access admin panel', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# --- UTILITY FUNCTIONS ---
def generate_booking_number():
    """Generate unique booking number with format: VR-YYYYMMDD-XXXX"""
    now = datetime.now()
    date_str = now.strftime('%Y%m%d')
    prefix = f'VR-{date_str}-'
    
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        today_start = now.strftime('%Y-%m-%d 00:00:00')
        
        cursor.execute(
            'SELECT COUNT(*) as count FROM bookings WHERE created_at >= %s',
            (today_start,)
        )
        today_count = cursor.fetchone()['count']
        
        sequence = str(today_count + 1).zfill(4)
        booking_number = prefix + sequence
        
        cursor.execute('SELECT id FROM bookings WHERE booking_number = %s', (booking_number,))
        while cursor.fetchone():
            today_count += 1
            sequence = str(today_count + 1).zfill(4)
            booking_number = prefix + sequence
            cursor.execute('SELECT id FROM bookings WHERE booking_number = %s', (booking_number,))
    
    return booking_number


def check_availability(vehicle_id, start_datetime, end_datetime):
    """Check if vehicle is available for given date range"""
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        query = '''
            SELECT * FROM bookings 
            WHERE vehicle_id = %s 
            AND status != 'cancelled'
            AND (start_date || ' ' || pickup_time)::timestamp < %s::timestamp
            AND (end_date || ' ' || return_time)::timestamp > %s::timestamp
        '''
        cursor.execute(query, (vehicle_id, end_datetime, start_datetime))
        conflict = cursor.fetchone()
        return conflict is None


def get_calendar_data(vehicle_id, year, month):
    """Generate calendar data with booking status"""
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        
        cursor.execute('''
            SELECT start_date, pickup_time, end_date, return_time, status 
            FROM bookings 
            WHERE vehicle_id = %s AND status != 'cancelled'
        ''', (vehicle_id,))
        
        bookings = cursor.fetchall()
    
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    
    last_day = (next_month - timedelta(days=1)).day
    day_status = {}
    
    for day in range(1, last_day + 1):
        current_date = datetime(year, month, day)
        morning_booked = False
        afternoon_booked = False
        
        for booking in bookings:
            try:
                start = datetime.strptime(f"{booking['start_date']} {booking['pickup_time']}", '%Y-%m-%d %H:%M')
                end = datetime.strptime(f"{booking['end_date']} {booking['return_time']}", '%Y-%m-%d %H:%M')
                
                if start.date() <= current_date.date() <= end.date():
                    if start.date() == current_date.date():
                        if start.hour < 12:
                            morning_booked = True
                        else:
                            afternoon_booked = True
                    elif end.date() == current_date.date():
                        if end.hour > 12:
                            afternoon_booked = True
                        else:
                            morning_booked = True
                    else:
                        morning_booked = True
                        afternoon_booked = True
            except:
                continue
        
        if morning_booked and afternoon_booked:
            day_status[day] = 'full'
        elif morning_booked or afternoon_booked:
            day_status[day] = 'half'
        else:
            day_status[day] = 'available'
    
    return {
        'year': year,
        'month': month,
        'days': day_status,
        'month_name': datetime(year, month, 1).strftime('%B'),
        'first_day': datetime(year, month, 1).weekday(),
        'last_day': last_day
    }


# --- PUBLIC ROUTES ---
@app.route('/')
def index():
    """Public catalog page with availability checking"""
    category = request.args.get('category', 'Motor')
    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')
    
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        cursor.execute(
            'SELECT * FROM vehicles WHERE is_active = 1 AND category = %s ORDER BY type, name',
            (category,)
        )
        vehicles_raw = cursor.fetchall()
    
    vehicles = []
    for vehicle in vehicles_raw:
        vehicle_dict = dict(vehicle)
        
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d %H:%M')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d %H:%M')
                
                start_str = start_dt.strftime('%Y-%m-%d %H:%M')
                end_str = end_dt.strftime('%Y-%m-%d %H:%M')
                
                vehicle_dict['available'] = check_availability(vehicle['id'], start_str, end_str)
            except:
                vehicle_dict['available'] = True
        else:
            vehicle_dict['available'] = True
        
        vehicles.append(vehicle_dict)
    
    return render_template('catalog.html', 
                         vehicles=vehicles, 
                         current_category=category,
                         start_date=start_date,
                         end_date=end_date,
                         whatsapp=WHATSAPP_NUMBER)


# --- AUTHENTICATION ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login"""
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            cursor.execute('SELECT * FROM admin_users WHERE user_id = %s', (user_id,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                session['admin_logged_in'] = True
                session['user_id'] = user['user_id']
                session['full_name'] = user['full_name']
                
                cursor.execute('UPDATE admin_users SET last_login = %s WHERE id = %s',
                            (datetime.now(), user['id']))
                
                flash('Login successful!', 'success')
                return redirect(url_for('admin_catalog'))
            else:
                flash('Invalid user ID or password!', 'error')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Admin logout"""
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))


# --- ADMIN USER MANAGEMENT ---
@app.route('/admin/users')
@login_required
def admin_users():
    """Manage admin users"""
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        cursor.execute('SELECT * FROM admin_users ORDER BY created_at DESC')
        users = cursor.fetchall()
    
    return render_template('admin_users.html', users=users)


@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
def admin_add_user():
    """Add new admin user"""
    if request.method == 'POST':
        try:
            user_id = request.form['user_id']
            password = request.form['password']
            full_name = request.form['full_name']
            
            password_hash = generate_password_hash(password)
            
            with get_db_connection() as conn:
                cursor = get_db_cursor(conn)
                cursor.execute(
                    'INSERT INTO admin_users (user_id, password_hash, full_name) VALUES (%s, %s, %s)',
                    (user_id, password_hash, full_name)
                )
            
            flash('Admin user added successfully!', 'success')
            return redirect(url_for('admin_users'))
        except psycopg2.IntegrityError:
            flash('User ID already exists!', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('admin_add_user.html')


@app.route('/admin/users/<int:id>/delete')
@login_required
def admin_delete_user(id):
    """Delete admin user"""
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        
        cursor.execute('SELECT user_id FROM admin_users WHERE id = %s', (id,))
        user = cursor.fetchone()
        
        if user and user['user_id'] == session.get('user_id'):
            flash('Cannot delete your own account!', 'error')
            return redirect(url_for('admin_users'))
        
        cursor.execute('SELECT COUNT(*) as cnt FROM admin_users')
        count = cursor.fetchone()['cnt']
        
        if count <= 1:
            flash('Cannot delete the last admin user!', 'error')
            return redirect(url_for('admin_users'))
        
        cursor.execute('DELETE FROM admin_users WHERE id = %s', (id,))
    
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_users'))


# --- ADMIN VEHICLE ROUTES ---
@app.route('/admin')
@login_required
def admin_catalog():
    """Admin vehicle catalog with search and filter"""
    search_query = request.args.get('search', '').strip()
    category = request.args.get('category', 'all')
    
    sql = "SELECT * FROM vehicles WHERE 1=1"
    params = []
    
    if category != 'all':
        sql += " AND category = %s"
        params.append(category)
    
    if search_query:
        sql += """ AND (
            name ILIKE %s OR 
            license_plate ILIKE %s OR 
            type ILIKE %s OR 
            cc::TEXT ILIKE %s
        )"""
        search_param = f"%{search_query}%"
        params.extend([search_param] * 4)
    
    sql += " ORDER BY is_active DESC, category, name ASC"
    
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        cursor.execute(sql, params)
        vehicles = cursor.fetchall()
        
        cursor.execute("SELECT COUNT(*) as total FROM vehicles")
        total_vehicles = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as active FROM vehicles WHERE is_active = 1")
        active_vehicles = cursor.fetchone()['active']
    
    return render_template('admin_catalog.html', 
                         vehicles=vehicles,
                         total_vehicles=total_vehicles,
                         active_vehicles=active_vehicles,
                         current_category=category)


@app.route('/admin/vehicle/add', methods=['GET', 'POST'])
@login_required
def admin_add_vehicle():
    """Add new vehicle"""
    if request.method == 'POST':
        try:
            image_path = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = secure_filename(f"{timestamp}_{file.filename}")
                    saved_path = compress_and_save_image(file, filename)
                    if saved_path:
                        image_path = f"/static/uploads/vehicles/{filename}"
            
            with get_db_connection() as conn:
                cursor = get_db_cursor(conn)
                cursor.execute('''INSERT INTO vehicles 
                    (name, type, cc, license_plate, category, price_day, price_3day, price_weekly, price_monthly, image_url, terms_and_conditions) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
                    (request.form['name'],
                     request.form['type'],
                     request.form['cc'],
                     request.form.get('license_plate', '').upper(),
                     request.form.get('category', 'Motor'),
                     request.form['price_day'],
                     request.form['price_3day'],
                     request.form['price_weekly'],
                     request.form['price_monthly'],
                     image_path,
                     request.form.get('terms_and_conditions', '')))
            
            flash('Vehicle added successfully!', 'success')
            return redirect(url_for('admin_catalog'))
        except psycopg2.IntegrityError as e:
            if 'license_plate' in str(e):
                flash('License plate already exists!', 'error')
            elif 'name' in str(e):
                flash('Vehicle name already exists!', 'error')
            else:
                flash(f'Error: {str(e)}', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('admin_add.html')


@app.route('/admin/vehicle/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_vehicle(id):
    """Edit vehicle"""
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        cursor.execute('SELECT * FROM vehicles WHERE id = %s', (id,))
        vehicle = cursor.fetchone()
    
    if not vehicle:
        flash('Vehicle not found!', 'error')
        return redirect(url_for('admin_catalog'))
    
    if request.method == 'POST':
        try:
            image_path = vehicle['image_url']
            
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = secure_filename(f"{timestamp}_{file.filename}")
                    
                    new_image_path = compress_and_save_image(file, filename)
                    if new_image_path:
                        if image_path and image_path.startswith('/static/'):
                            old_path = image_path.lstrip('/')
                            if os.path.exists(old_path):
                                try:
                                    os.remove(old_path)
                                except:
                                    pass
                        
                        image_path = f"/static/uploads/vehicles/{filename}"
            
            with get_db_connection() as conn:
                cursor = get_db_cursor(conn)
                cursor.execute('''UPDATE vehicles SET 
                    name=%s, type=%s, cc=%s, license_plate=%s, category=%s,
                    price_day=%s, price_3day=%s, price_weekly=%s, price_monthly=%s, 
                    image_url=%s, terms_and_conditions=%s
                    WHERE id=%s''', 
                    (request.form['name'],
                     request.form['type'],
                     request.form['cc'],
                     request.form.get('license_plate', '').upper(),
                     request.form.get('category', 'Motor'),
                     request.form['price_day'],
                     request.form['price_3day'],
                     request.form['price_weekly'],
                     request.form['price_monthly'],
                     image_path,
                     request.form.get('terms_and_conditions', ''),
                     id))
            
            flash('Vehicle updated successfully!', 'success')
            return redirect(url_for('admin_detail', id=id))
        except psycopg2.IntegrityError as e:
            if 'license_plate' in str(e):
                flash('License plate already exists!', 'error')
            elif 'name' in str(e):
                flash('Vehicle name already exists!', 'error')
            else:
                flash(f'Error: {str(e)}', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('admin_edit.html', vehicle=vehicle)


@app.route('/admin/vehicle/<int:id>/toggle')
@login_required
def admin_toggle_vehicle(id):
    """Toggle vehicle active status"""
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        cursor.execute('SELECT is_active FROM vehicles WHERE id = %s', (id,))
        vehicle = cursor.fetchone()
        
        if vehicle:
            new_status = 0 if vehicle['is_active'] == 1 else 1
            cursor.execute('UPDATE vehicles SET is_active = %s WHERE id = %s', (new_status, id))
            
            status_text = 'activated' if new_status == 1 else 'deactivated'
            flash(f'Vehicle {status_text} successfully!', 'success')
        else:
            flash('Vehicle not found!', 'error')
    
    return redirect(url_for('admin_catalog'))


@app.route('/admin/vehicle/<int:id>')
@login_required
def admin_detail(id):
    """View vehicle details"""
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        cursor.execute('SELECT * FROM vehicles WHERE id = %s', (id,))
        vehicle = cursor.fetchone()
        
        if not vehicle:
            flash('Vehicle not found!', 'error')
            return redirect(url_for('admin_catalog'))
        
        cursor.execute('''SELECT * FROM bookings 
                        WHERE vehicle_id = %s 
                        ORDER BY created_at DESC, start_date DESC''', 
                     (id,))
        bookings = cursor.fetchall()
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    calendar_data = get_calendar_data(id, current_year, current_month)
    
    return render_template('admin_detail.html', 
                         vehicle=vehicle, 
                         bookings=bookings,
                         current_year=current_year,
                         current_month=current_month,
                         calendar_data=calendar_data)


@app.route('/admin/vehicle/<int:id>/calendar/<int:year>/<int:month>')
@login_required
def get_vehicle_calendar(id, year, month):
    """Get calendar data"""
    calendar_data = get_calendar_data(id, year, month)
    return jsonify(calendar_data)


# --- ON RENT ROUTE ---
@app.route('/admin/on-rent')
@login_required
def admin_on_rent():
    """View currently rented vehicles - SIMPLIFIED VERSION"""
    
    # Get ALL confirmed/pending bookings first
    query = '''
        SELECT 
            b.*, 
            v.name as vehicle_name, 
            v.license_plate, 
            v.type as vehicle_type, 
            v.category
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        WHERE b.status IN ('confirmed', 'pending')
        ORDER BY b.end_date ASC, b.return_time ASC
    '''
    
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        cursor.execute(query)
        all_bookings = cursor.fetchall()
    
    # Filter di Python instead of SQL (lebih reliable)
    from datetime import datetime
    now = datetime.now()
    
    on_rent = []
    for booking in all_bookings:
        try:
            # Parse start datetime
            start_dt = datetime.strptime(
                f"{booking['start_date']} {booking['pickup_time']}", 
                '%Y-%m-%d %H:%M'
            )
            
            # Parse end datetime
            end_dt = datetime.strptime(
                f"{booking['end_date']} {booking['return_time']}", 
                '%Y-%m-%d %H:%M'
            )
            
            # Check if currently on rent
            if start_dt <= now <= end_dt:
                on_rent.append(booking)
                print(f"✅ ON RENT: {booking['booking_number']} - {booking['vehicle_name']}")
        except Exception as e:
            print(f"❌ Error parsing booking {booking.get('id')}: {e}")
            continue
    
    print(f"\n📊 Total confirmed/pending: {len(all_bookings)}")
    print(f"🔄 Currently on rent: {len(on_rent)}")
    
    return render_template('admin_on_rent.html', bookings=on_rent)


# --- BOOKING ROUTES ---
@app.route('/admin/booking/add/<int:vehicle_id>', methods=['POST'])
@login_required
def admin_add_booking(vehicle_id):
    """Add booking"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            cursor.execute('SELECT * FROM vehicles WHERE id = %s', (vehicle_id,))
            vehicle = cursor.fetchone()
            
            if not vehicle:
                flash('Vehicle not found!', 'error')
                return redirect(url_for('admin_catalog'))
            
            booking_number = generate_booking_number()
            
            customer_photo_path = None
            if 'customer_photo' in request.files:
                file = request.files['customer_photo']
                if file and file.filename and allowed_file(file.filename):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = secure_filename(f"customer_{timestamp}_{file.filename}")
                    saved_path = compress_and_save_image(file, filename, CUSTOMER_PHOTO_FOLDER)
                    if saved_path:
                        customer_photo_path = f"/static/uploads/customers/{filename}"
            
            total_price = request.form.get('total_price', '')
            try:
                total_price = float(total_price) if total_price else None
            except:
                total_price = None
            
            cursor.execute('''INSERT INTO bookings 
                (booking_number, vehicle_id, customer_name, ic_number, nationality, customer_photo, location, destination,
                 start_date, pickup_time, end_date, return_time, total_price, status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
                (booking_number,
                 vehicle_id,
                 request.form['customer_name'],
                 request.form.get('ic_number', ''),
                 request.form.get('nationality', 'Malaysian'),
                 customer_photo_path,
                 request.form.get('location', ''),
                 request.form.get('destination', ''),
                 request.form['start_date'],
                 request.form['pickup_time'],
                 request.form['end_date'],
                 request.form['return_time'],
                 total_price,
                 request.form.get('status', 'confirmed')))
        
        flash(f'Booking added! Number: {booking_number}', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_detail', id=vehicle_id))


@app.route('/admin/booking/<int:id>/edit', methods=['POST'])
@login_required
def admin_edit_booking(id):
    """Edit booking"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            cursor.execute('SELECT vehicle_id, customer_photo FROM bookings WHERE id = %s', (id,))
            booking = cursor.fetchone()
            
            if not booking:
                flash('Booking not found!', 'error')
                return redirect(url_for('admin_catalog'))
            
            customer_photo_path = booking['customer_photo']
            if 'customer_photo' in request.files:
                file = request.files['customer_photo']
                if file and file.filename and allowed_file(file.filename):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = secure_filename(f"customer_{timestamp}_{file.filename}")
                    
                    saved_path = compress_and_save_image(file, filename, CUSTOMER_PHOTO_FOLDER)
                    if saved_path:
                        if customer_photo_path and customer_photo_path.startswith('/static/'):
                            old_path = customer_photo_path.lstrip('/')
                            if os.path.exists(old_path):
                                try:
                                    os.remove(old_path)
                                except:
                                    pass
                        
                        customer_photo_path = f"/static/uploads/customers/{filename}"
            
            total_price = request.form.get('total_price', '')
            try:
                total_price = float(total_price) if total_price else None
            except:
                total_price = None
            
            cursor.execute('''UPDATE bookings SET 
                customer_name=%s, ic_number=%s, nationality=%s, customer_photo=%s, location=%s, destination=%s,
                start_date=%s, pickup_time=%s, end_date=%s, return_time=%s, total_price=%s, status=%s
                WHERE id=%s''', 
                (request.form['customer_name'],
                 request.form.get('ic_number', ''),
                 request.form.get('nationality', 'Malaysian'),
                 customer_photo_path,
                 request.form.get('location', ''),
                 request.form.get('destination', ''),
                 request.form['start_date'],
                 request.form['pickup_time'],
                 request.form['end_date'],
                 request.form['return_time'],
                 total_price,
                 request.form.get('status', 'confirmed'),
                 id))
        
        flash('Booking updated!', 'success')
        return redirect(url_for('admin_detail', id=booking['vehicle_id']))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(request.referrer or url_for('admin_catalog'))


@app.route('/admin/booking/<int:id>/delete')
@login_required
def admin_delete_booking(id):
    """Delete booking"""
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        cursor.execute('SELECT vehicle_id, customer_photo FROM bookings WHERE id = %s', (id,))
        booking = cursor.fetchone()
        
        if booking:
            if booking['customer_photo'] and booking['customer_photo'].startswith('/static/'):
                photo_path = booking['customer_photo'].lstrip('/')
                if os.path.exists(photo_path):
                    try:
                        os.remove(photo_path)
                    except:
                        pass
            
            cursor.execute('DELETE FROM bookings WHERE id = %s', (id,))
            flash('Booking deleted!', 'success')
            return redirect(url_for('admin_detail', id=booking['vehicle_id']))
    
    flash('Booking not found!', 'error')
    return redirect(url_for('admin_catalog'))


@app.route('/admin/booking/<int:id>/update-status', methods=['POST'])
@login_required
def admin_update_booking_status(id):
    """Update booking status via AJAX"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['pending', 'confirmed', 'cancelled', 'completed']:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            cursor.execute('UPDATE bookings SET status = %s WHERE id = %s', (new_status, id))
        
        return jsonify({'success': True, 'message': 'Status updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# --- ALL BOOKINGS (OPTIMIZED) ---
@app.route('/admin/bookings')
@login_required
def admin_all_bookings():
    """Optimized all bookings with pagination"""
    status_filter = request.args.get('status', 'all')
    vehicle_filter = request.args.get('vehicle', 'all')
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', 'newest')
    page = int(request.args.get('page', 1))
    
    current_month = datetime.now().strftime('%Y-%m')
    month_filter = request.args.get('month', current_month)
    show_all = request.args.get('show_all', '0') == '1'
    
    query = '''
        SELECT b.*, v.name as vehicle_name, v.license_plate, v.type as vehicle_type
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        WHERE 1=1
    '''
    params = []
    
    if not show_all and month_filter:
        query += ' AND SUBSTRING(b.start_date FROM 1 FOR 7) = %s'
        params.append(month_filter)
    
    if status_filter != 'all':
        query += ' AND b.status = %s'
        params.append(status_filter)
    
    if vehicle_filter and vehicle_filter != 'all':
        try:
            query += ' AND b.vehicle_id = %s'
            params.append(int(vehicle_filter))
        except (ValueError, TypeError):
            pass
    
    if search_query:
        query += ''' AND (
            b.booking_number ILIKE %s OR 
            b.customer_name ILIKE %s OR 
            b.ic_number ILIKE %s OR
            v.name ILIKE %s OR
            v.license_plate ILIKE %s
        )'''
        search_param = f'%{search_query}%'
        params.extend([search_param] * 5)
    
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        
        count_query = f"SELECT COUNT(*) as total FROM ({query}) as count_query"
        cursor.execute(count_query, params)
        total_bookings = cursor.fetchone()['total']
        total_pages = (total_bookings + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        
        if sort_by == 'newest':
            query += ' ORDER BY b.created_at DESC'
        elif sort_by == 'oldest':
            query += ' ORDER BY b.created_at ASC'
        elif sort_by == 'start_date':
            query += ' ORDER BY b.start_date DESC'
        elif sort_by == 'customer':
            query += ' ORDER BY b.customer_name ASC'
        
        offset = (page - 1) * ITEMS_PER_PAGE
        query += f' LIMIT {ITEMS_PER_PAGE} OFFSET {offset}'
        
        cursor.execute(query, params)
        bookings = cursor.fetchall()
        
        cursor.execute('SELECT id, name, license_plate FROM vehicles ORDER BY name')
        vehicles = cursor.fetchall()
    
    stats = {
        'total': total_bookings,
        'confirmed': len([b for b in bookings if b['status'] == 'confirmed']),
        'pending': len([b for b in bookings if b['status'] == 'pending']),
        'cancelled': len([b for b in bookings if b['status'] == 'cancelled']),
        'completed': len([b for b in bookings if b['status'] == 'completed'])
    }
    
    return render_template('admin_all_bookings.html',
                         bookings=bookings,
                         vehicles=vehicles,
                         stats=stats,
                         current_status=status_filter,
                         current_vehicle=vehicle_filter,
                         current_search=search_query,
                         current_sort=sort_by,
                         current_month=month_filter,
                         show_all=show_all,
                         page=page,
                         total_pages=total_pages,
                         total_bookings=total_bookings)


@app.route('/admin/bookings/print')
@login_required
def print_bookings_report():
    """Print report"""
    status_filter = request.args.get('status', 'all')
    vehicle_filter = request.args.get('vehicle', 'all')
    
    current_month = datetime.now().strftime('%Y-%m')
    month_filter = request.args.get('month', current_month)
    
    query = '''
        SELECT b.*, v.name as vehicle_name, v.license_plate, v.type as vehicle_type
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        WHERE SUBSTRING(b.start_date FROM 1 FOR 7) = %s
    '''
    params = [month_filter]
    
    if status_filter != 'all':
        query += ' AND b.status = %s'
        params.append(status_filter)
    
    if vehicle_filter != 'all':
        try:
            query += ' AND b.vehicle_id = %s'
            params.append(int(vehicle_filter))
        except:
            pass
    
    query += ' ORDER BY b.created_at DESC LIMIT 500'
    
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        cursor.execute(query, params)
        bookings = cursor.fetchall()
    
    stats = {
        'total': len(bookings),
        'confirmed': len([b for b in bookings if b['status'] == 'confirmed']),
        'pending': len([b for b in bookings if b['status'] == 'pending']),
        'cancelled': len([b for b in bookings if b['status'] == 'cancelled']),
        'completed': len([b for b in bookings if b['status'] == 'completed'])
    }
    
    return render_template('print_bookings.html', 
                         bookings=bookings,
                         stats=stats,
                         report_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                         current_month=month_filter)


# --- ERROR HANDLERS ---
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


# --- STARTUP ---
if __name__ == '__main__':
    print("\n" + "="*70)
    print("VehicleRent Application Starting...")
    print("="*70)
    
    print("\nChecking database connection...")
    try:
        init_db()
        print("Connected to PostgreSQL/Supabase successfully!")
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("\n Please check your environment variables!")
        print("Set either DATABASE_URL or individual SUPABASE_* variables")
        exit(1)
    
    print("\nApplication Ready!")
    print("="*70 + "\n")
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') != 'production'
    
    app.run(debug=debug, host='0.0.0.0', port=port)
