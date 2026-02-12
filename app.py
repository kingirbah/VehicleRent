from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import io
from PIL import Image

app = Flask(__name__)
app.secret_key = "vehiclesrent_v7_ultra_secure_key_2026_production"

# --- CONFIGURATION ---
WHATSAPP_NUMBER = "6285111040408"

# Upload configuration
UPLOAD_FOLDER = 'static/uploads/vehicles'
CUSTOMER_PHOTO_FOLDER = 'static/uploads/customers'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB

# Pagination
ITEMS_PER_PAGE = 50

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CUSTOMER_PHOTO_FOLDER, exist_ok=True)


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


# --- DATABASE MANAGEMENT ---
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with all required tables"""
    with get_db() as conn:
        # Admin Users Table
        conn.execute('''CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )''')
        
        # Vehicles Table
        conn.execute('''CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT UNIQUE NOT NULL, 
            type TEXT NOT NULL, 
            cc TEXT NOT NULL,
            license_plate TEXT UNIQUE,
            category TEXT DEFAULT 'Motor',
            price_day INTEGER NOT NULL, 
            price_3day INTEGER NOT NULL, 
            price_weekly INTEGER NOT NULL, 
            price_monthly INTEGER NOT NULL,
            image_url TEXT,
            terms_and_conditions TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Bookings Table
        conn.execute('''CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_number TEXT UNIQUE NOT NULL,
            vehicle_id INTEGER NOT NULL, 
            customer_name TEXT NOT NULL, 
            ic_number TEXT,
            nationality TEXT DEFAULT 'Malaysian',
            customer_photo TEXT,
            location TEXT, 
            destination TEXT,
            start_date TEXT NOT NULL, 
            pickup_time TEXT NOT NULL, 
            end_date TEXT NOT NULL, 
            return_time TEXT NOT NULL,
            total_price REAL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE
        )''')
        
        # Create indexes
        conn.execute('CREATE INDEX IF NOT EXISTS idx_bookings_vehicle ON bookings(vehicle_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_bookings_created ON bookings(created_at)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_bookings_dates ON bookings(start_date, end_date)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_bookings_month ON bookings(substr(start_date, 1, 7))')
        
        # Check and add missing columns
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(vehicles)")
        vehicle_columns = [column[1] for column in cursor.fetchall()]
        
        if 'license_plate' not in vehicle_columns:
            conn.execute("ALTER TABLE vehicles ADD COLUMN license_plate TEXT")
            print("  ✓ Added column: license_plate")
        
        if 'category' not in vehicle_columns:
            conn.execute("ALTER TABLE vehicles ADD COLUMN category TEXT DEFAULT 'Motor'")
            conn.execute("UPDATE vehicles SET category = 'Motor' WHERE category IS NULL")
            print("  ✓ Added column: category")
        
        if 'image_url' not in vehicle_columns:
            conn.execute("ALTER TABLE vehicles ADD COLUMN image_url TEXT")
            print("  ✓ Added column: image_url")
        
        if 'terms_and_conditions' not in vehicle_columns:
            conn.execute("ALTER TABLE vehicles ADD COLUMN terms_and_conditions TEXT")
            print("  ✓ Added column: terms_and_conditions")
        
        cursor.execute("PRAGMA table_info(bookings)")
        booking_columns = [column[1] for column in cursor.fetchall()]
        
        if 'booking_number' not in booking_columns:
            conn.execute("ALTER TABLE bookings ADD COLUMN booking_number TEXT")
            
            cursor.execute("SELECT id, created_at FROM bookings WHERE booking_number IS NULL OR booking_number = ''")
            existing_bookings = cursor.fetchall()
            
            if existing_bookings:
                date_counters = {}
                for booking in existing_bookings:
                    booking_id = booking[0]
                    created_at = booking[1] or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    date_str = created_at.split(' ')[0].replace('-', '')
                    
                    if date_str not in date_counters:
                        date_counters[date_str] = 0
                    
                    date_counters[date_str] += 1
                    sequence = str(date_counters[date_str]).zfill(4)
                    booking_number = f'VR-{date_str}-{sequence}'
                    
                    conn.execute("UPDATE bookings SET booking_number = ? WHERE id = ?", 
                               (booking_number, booking_id))
        
        if 'nationality' not in booking_columns:
            conn.execute("ALTER TABLE bookings ADD COLUMN nationality TEXT DEFAULT 'Malaysian'")
            print("  ✓ Added column: nationality")
        
        if 'customer_photo' not in booking_columns:
            conn.execute("ALTER TABLE bookings ADD COLUMN customer_photo TEXT")
            print("  ✓ Added column: customer_photo")
        
        if 'total_price' not in booking_columns:
            conn.execute("ALTER TABLE bookings ADD COLUMN total_price REAL")
            print("  ✓ Added column: total_price")
        
        # Create default admin if no users exist
        cursor.execute("SELECT COUNT(*) FROM admin_users")
        if cursor.fetchone()[0] == 0:
            default_hash = generate_password_hash('admin123')
            conn.execute(
                "INSERT INTO admin_users (user_id, password_hash, full_name) VALUES (?, ?, ?)",
                ('admin', default_hash, 'Administrator')
            )
            print("Default admin created - user_id: admin, password: admin123")
        
        conn.commit()
    print("Database initialized successfully!")


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
    # FIXED: Use 2026-02-10 as the current date
    now = datetime(2026, 2, 10)
    date_str = now.strftime('%Y%m%d')
    prefix = f'VR-{date_str}-'
    
    db = get_db()
    today_start = now.strftime('%Y-%m-%d 00:00:00')
    today_count = db.execute(
        'SELECT COUNT(*) as count FROM bookings WHERE created_at >= ?',
        (today_start,)
    ).fetchone()['count']
    
    sequence = str(today_count + 1).zfill(4)
    booking_number = prefix + sequence
    
    while db.execute('SELECT id FROM bookings WHERE booking_number = ?', (booking_number,)).fetchone():
        today_count += 1
        sequence = str(today_count + 1).zfill(4)
        booking_number = prefix + sequence
    
    return booking_number


def check_availability(vehicle_id, start_datetime, end_datetime):
    """Check if vehicle is available for given date range"""
    db = get_db()
    query = '''
        SELECT * FROM bookings 
        WHERE vehicle_id = ? 
        AND status != 'cancelled'
        AND datetime(start_date || " " || pickup_time) < datetime(?) 
        AND datetime(end_date || " " || return_time) > datetime(?)
    '''
    conflict = db.execute(query, (vehicle_id, end_datetime, start_datetime)).fetchone()
    return conflict is None


def get_calendar_data(vehicle_id, year, month):
    """Generate calendar data with booking status"""
    db = get_db()
    
    bookings = db.execute('''
        SELECT start_date, pickup_time, end_date, return_time, status 
        FROM bookings 
        WHERE vehicle_id = ? AND status != 'cancelled'
    ''', (vehicle_id,)).fetchall()
    
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
    db = get_db()
    category = request.args.get('category', 'Motor')
    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')
    
    # Get all active vehicles in category
    vehicles_raw = db.execute(
        'SELECT * FROM vehicles WHERE is_active = 1 AND category = ? ORDER BY type, name',
        (category,)
    ).fetchall()
    
    # Convert to list of dicts and check availability
    vehicles = []
    for vehicle in vehicles_raw:
        vehicle_dict = dict(vehicle)
        
        # Check availability ONLY if dates are provided
        if start_date and end_date:
            try:
                # Parse dates
                start_dt = datetime.strptime(start_date, '%Y-%m-%d %H:%M')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d %H:%M')
                
                # Format for database query
                start_str = start_dt.strftime('%Y-%m-%d %H:%M')
                end_str = end_dt.strftime('%Y-%m-%d %H:%M')
                
                # Check if available
                vehicle_dict['available'] = check_availability(vehicle['id'], start_str, end_str)
            except:
                # If date parsing fails, show as available
                vehicle_dict['available'] = True
        else:
            # IMPORTANT: When NO dates selected, default to True (show Available badge)
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
        
        db = get_db()
        user = db.execute('SELECT * FROM admin_users WHERE user_id = ?', (user_id,)).fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            session['admin_logged_in'] = True
            session['user_id'] = user['user_id']
            session['full_name'] = user['full_name']
            
            db.execute('UPDATE admin_users SET last_login = ? WHERE id = ?',
                      (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user['id']))
            db.commit()
            
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
    db = get_db()
    users = db.execute('SELECT * FROM admin_users ORDER BY created_at DESC').fetchall()
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
            
            db = get_db()
            db.execute(
                'INSERT INTO admin_users (user_id, password_hash, full_name) VALUES (?, ?, ?)',
                (user_id, password_hash, full_name)
            )
            db.commit()
            
            flash('Admin user added successfully!', 'success')
            return redirect(url_for('admin_users'))
        except sqlite3.IntegrityError:
            flash('User ID already exists!', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('admin_add_user.html')


@app.route('/admin/users/<int:id>/delete')
@login_required
def admin_delete_user(id):
    """Delete admin user"""
    db = get_db()
    
    # Prevent deleting yourself
    user = db.execute('SELECT user_id FROM admin_users WHERE id = ?', (id,)).fetchone()
    if user and user['user_id'] == session.get('user_id'):
        flash('Cannot delete your own account!', 'error')
        return redirect(url_for('admin_users'))
    
    # Ensure at least one admin remains
    count = db.execute('SELECT COUNT(*) as cnt FROM admin_users').fetchone()['cnt']
    if count <= 1:
        flash('Cannot delete the last admin user!', 'error')
        return redirect(url_for('admin_users'))
    
    db.execute('DELETE FROM admin_users WHERE id = ?', (id,))
    db.commit()
    flash('User deleted successfully!', 'success')
    
    return redirect(url_for('admin_users'))


# --- ADMIN VEHICLE ROUTES ---
@app.route('/admin')
@login_required
def admin_catalog():
    """Admin vehicle catalog with search and filter"""
    db = get_db()
    
    # Get search and filter parameters
    search_query = request.args.get('search', '').strip()
    category = request.args.get('category', 'all')
    
    # Build SQL query
    sql = "SELECT * FROM vehicles WHERE 1=1"
    params = []
    
    # Add category filter
    if category != 'all':
        sql += " AND category = ?"
        params.append(category)
    
    # Add search filter (searches in multiple fields)
    if search_query:
        sql += """ AND (
            name LIKE ? OR 
            license_plate LIKE ? OR 
            type LIKE ? OR 
            CAST(cc AS TEXT) LIKE ?
        )"""
        search_param = f"%{search_query}%"
        params.extend([search_param, search_param, search_param, search_param])
    
    # Order by active status and name
    sql += " ORDER BY is_active DESC, category, name ASC"
    
    # Execute query
    vehicles = db.execute(sql, params).fetchall()
    
    # Get statistics for all vehicles (ignoring filters for dashboard stats)
    total_vehicles = db.execute("SELECT COUNT(*) as total FROM vehicles").fetchone()['total']
    active_vehicles = db.execute("SELECT COUNT(*) as active FROM vehicles WHERE is_active = 1").fetchone()['active']
    
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
            db = get_db()
            
            image_path = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = secure_filename(f"{timestamp}_{file.filename}")
                    image_path = compress_and_save_image(file, filename)
                    if image_path:
                        image_path = f"/static/uploads/vehicles/{filename}"
            
            db.execute('''INSERT INTO vehicles 
                (name, type, cc, license_plate, category, price_day, price_3day, price_weekly, price_monthly, image_url, terms_and_conditions) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
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
            db.commit()
            flash('Vehicle added successfully!', 'success')
            return redirect(url_for('admin_catalog'))
        except sqlite3.IntegrityError as e:
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
    db = get_db()
    vehicle = db.execute('SELECT * FROM vehicles WHERE id = ?', (id,)).fetchone()
    
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
            
            db.execute('''UPDATE vehicles SET 
                name=?, type=?, cc=?, license_plate=?, category=?,
                price_day=?, price_3day=?, price_weekly=?, price_monthly=?, 
                image_url=?, terms_and_conditions=?
                WHERE id=?''', 
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
            db.commit()
            flash('Vehicle updated successfully!', 'success')
            return redirect(url_for('admin_detail', id=id))
        except sqlite3.IntegrityError as e:
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
    db = get_db()
    vehicle = db.execute('SELECT is_active FROM vehicles WHERE id = ?', (id,)).fetchone()
    
    if vehicle:
        new_status = 0 if vehicle['is_active'] == 1 else 1
        db.execute('UPDATE vehicles SET is_active = ? WHERE id = ?', (new_status, id))
        db.commit()
        status_text = 'activated' if new_status == 1 else 'deactivated'
        flash(f'Vehicle {status_text} successfully!', 'success')
    else:
        flash('Vehicle not found!', 'error')
    
    return redirect(url_for('admin_catalog'))


@app.route('/admin/vehicle/<int:id>')
@login_required
def admin_detail(id):
    """View vehicle details"""
    db = get_db()
    vehicle = db.execute('SELECT * FROM vehicles WHERE id = ?', (id,)).fetchone()
    
    if not vehicle:
        flash('Vehicle not found!', 'error')
        return redirect(url_for('admin_catalog'))
    
    bookings_raw = db.execute('''SELECT * FROM bookings 
                            WHERE vehicle_id = ? 
                            ORDER BY created_at DESC, start_date DESC''', 
                         (id,)).fetchall()
    
    bookings = [dict(row) for row in bookings_raw]
    
    # FIXED: Use 2026 as current year instead of system date
    current_year = 2026
    current_month = 2  # February 2026
    
    # Get calendar data for current month
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
    """View currently rented vehicles"""
    db = get_db()
    
    # FIXED: Use 2026-02-10 as current date
    today = datetime(2026, 2, 10).strftime('%Y-%m-%d %H:%M')
    
    query = '''
        SELECT b.*, v.name as vehicle_name, v.license_plate, v.type as vehicle_type, v.category
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        WHERE b.status IN ('confirmed', 'pending')
        AND datetime(b.start_date || " " || b.pickup_time) <= datetime(?)
        AND datetime(b.end_date || " " || b.return_time) >= datetime(?)
        ORDER BY b.end_date ASC, b.return_time ASC
    '''
    
    on_rent_raw = db.execute(query, (today, today)).fetchall()
    on_rent = [dict(row) for row in on_rent_raw]
    
    return render_template('admin_on_rent.html', bookings=on_rent)


# --- BOOKING ROUTES ---
@app.route('/admin/booking/add/<int:vehicle_id>', methods=['POST'])
@login_required
def admin_add_booking(vehicle_id):
    """Add booking"""
    try:
        db = get_db()
        
        vehicle = db.execute('SELECT * FROM vehicles WHERE id = ?', (vehicle_id,)).fetchone()
        if not vehicle:
            flash('Vehicle not found!', 'error')
            return redirect(url_for('admin_catalog'))
        
        booking_number = generate_booking_number()
        
        # Handle customer photo upload
        customer_photo_path = None
        if 'customer_photo' in request.files:
            file = request.files['customer_photo']
            if file and file.filename and allowed_file(file.filename):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = secure_filename(f"customer_{timestamp}_{file.filename}")
                saved_path = compress_and_save_image(file, filename, CUSTOMER_PHOTO_FOLDER)
                if saved_path:
                    customer_photo_path = f"/static/uploads/customers/{filename}"
        
        # Get total price from form
        total_price = request.form.get('total_price', '')
        try:
            total_price = float(total_price) if total_price else None
        except:
            total_price = None
        
        db.execute('''INSERT INTO bookings 
            (booking_number, vehicle_id, customer_name, ic_number, nationality, customer_photo, location, destination,
             start_date, pickup_time, end_date, return_time, total_price, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
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
        db.commit()
        flash(f'Booking added! Number: {booking_number}', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_detail', id=vehicle_id))


@app.route('/admin/booking/<int:id>/edit', methods=['POST'])
@login_required
def admin_edit_booking(id):
    """Edit booking"""
    try:
        db = get_db()
        booking = db.execute('SELECT vehicle_id, customer_photo FROM bookings WHERE id = ?', (id,)).fetchone()
        
        if not booking:
            flash('Booking not found!', 'error')
            return redirect(url_for('admin_catalog'))
        
        # Handle customer photo upload
        customer_photo_path = booking['customer_photo']
        if 'customer_photo' in request.files:
            file = request.files['customer_photo']
            if file and file.filename and allowed_file(file.filename):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = secure_filename(f"customer_{timestamp}_{file.filename}")
                
                saved_path = compress_and_save_image(file, filename, CUSTOMER_PHOTO_FOLDER)
                if saved_path:
                    # Delete old photo
                    if customer_photo_path and customer_photo_path.startswith('/static/'):
                        old_path = customer_photo_path.lstrip('/')
                        if os.path.exists(old_path):
                            try:
                                os.remove(old_path)
                            except:
                                pass
                    
                    customer_photo_path = f"/static/uploads/customers/{filename}"
        
        # Get total price from form
        total_price = request.form.get('total_price', '')
        try:
            total_price = float(total_price) if total_price else None
        except:
            total_price = None
        
        db.execute('''UPDATE bookings SET 
            customer_name=?, ic_number=?, nationality=?, customer_photo=?, location=?, destination=?,
            start_date=?, pickup_time=?, end_date=?, return_time=?, total_price=?, status=?
            WHERE id=?''', 
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
        db.commit()
        flash('Booking updated!', 'success')
        return redirect(url_for('admin_detail', id=booking['vehicle_id']))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(request.referrer or url_for('admin_catalog'))


@app.route('/admin/booking/<int:id>/delete')
@login_required
def admin_delete_booking(id):
    """Delete booking"""
    db = get_db()
    booking = db.execute('SELECT vehicle_id, customer_photo FROM bookings WHERE id = ?', (id,)).fetchone()
    
    if booking:
        # Delete customer photo if exists
        if booking['customer_photo'] and booking['customer_photo'].startswith('/static/'):
            photo_path = booking['customer_photo'].lstrip('/')
            if os.path.exists(photo_path):
                try:
                    os.remove(photo_path)
                except:
                    pass
        
        db.execute('DELETE FROM bookings WHERE id = ?', (id,))
        db.commit()
        flash('Booking deleted!', 'success')
        return redirect(url_for('admin_detail', id=booking['vehicle_id']))
    
    flash('Booking not found!', 'error')
    return redirect(url_for('admin_catalog'))


# --- BOOKING STATUS UPDATE (NEW ROUTE) ---
@app.route('/admin/booking/<int:id>/update-status', methods=['POST'])
@login_required
def admin_update_booking_status(id):
    """Update booking status via AJAX"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['pending', 'confirmed', 'cancelled', 'completed']:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
        db = get_db()
        db.execute('UPDATE bookings SET status = ? WHERE id = ?', (new_status, id))
        db.commit()
        
        return jsonify({'success': True, 'message': 'Status updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# --- ALL BOOKINGS (OPTIMIZED WITH FIX) ---
@app.route('/admin/bookings')
@login_required
def admin_all_bookings():
    """Optimized all bookings with pagination - FIXED: Row to dict conversion"""
    db = get_db()
    
    # Get parameters
    status_filter = request.args.get('status', 'all')
    vehicle_filter = request.args.get('vehicle', 'all')
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', 'newest')
    page = int(request.args.get('page', 1))
    
    # Month filter - FIXED: default to 2026-02 instead of system date
    month_filter = request.args.get('month', '2026-02')
    show_all = request.args.get('show_all', '0') == '1'
    
    # Base query
    query = '''
        SELECT b.*, v.name as vehicle_name, v.license_plate, v.type as vehicle_type
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        WHERE 1=1
    '''
    params = []
    
    # Month filter
    if not show_all and month_filter:
        query += ' AND substr(b.start_date, 1, 7) = ?'
        params.append(month_filter)
    
    # Status filter
    if status_filter != 'all':
        query += ' AND b.status = ?'
        params.append(status_filter)
    
    # Vehicle filter
    if vehicle_filter and vehicle_filter != 'all':
        try:
            query += ' AND b.vehicle_id = ?'
            params.append(int(vehicle_filter))
        except (ValueError, TypeError):
            pass
    
    # Search
    if search_query:
        query += ''' AND (
            b.booking_number LIKE ? OR 
            b.customer_name LIKE ? OR 
            b.ic_number LIKE ? OR
            v.name LIKE ? OR
            v.license_plate LIKE ?
        )'''
        search_param = f'%{search_query}%'
        params.extend([search_param] * 5)
    
    # Count total for pagination
    count_query = f"SELECT COUNT(*) as total FROM ({query})"
    total_bookings = db.execute(count_query, params).fetchone()['total']
    total_pages = (total_bookings + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    # Sorting
    if sort_by == 'newest':
        query += ' ORDER BY b.created_at DESC'
    elif sort_by == 'oldest':
        query += ' ORDER BY b.created_at ASC'
    elif sort_by == 'start_date':
        query += ' ORDER BY b.start_date DESC'
    elif sort_by == 'customer':
        query += ' ORDER BY b.customer_name ASC'
    
    # Pagination
    offset = (page - 1) * ITEMS_PER_PAGE
    query += f' LIMIT {ITEMS_PER_PAGE} OFFSET {offset}'
    
    # FIXED: Convert Row objects to dictionaries for JSON serialization
    bookings_raw = db.execute(query, params).fetchall()
    bookings = [dict(row) for row in bookings_raw]
    
    # Get vehicles for filter
    vehicles = db.execute('SELECT id, name, license_plate FROM vehicles ORDER BY name').fetchall()
    
    # Stats (only for current view)
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
    db = get_db()
    
    status_filter = request.args.get('status', 'all')
    vehicle_filter = request.args.get('vehicle', 'all')
    # FIXED: default to 2026-02
    month_filter = request.args.get('month', '2026-02')
    
    query = '''
        SELECT b.*, v.name as vehicle_name, v.license_plate, v.type as vehicle_type
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        WHERE substr(b.start_date, 1, 7) = ?
    '''
    params = [month_filter]
    
    if status_filter != 'all':
        query += ' AND b.status = ?'
        params.append(status_filter)
    
    if vehicle_filter != 'all':
        query += ' AND b.vehicle_id = ?'
        params.append(int(vehicle_filter))
    
    query += ' ORDER BY b.created_at DESC LIMIT 500'
    
    bookings_raw = db.execute(query, params).fetchall()
    bookings = [dict(row) for row in bookings_raw]
    
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
    if not os.path.exists('database.db'):
        print("\nInitializing new database...")
        init_db()
    else:
        print("\nChecking database schema...")
        init_db()
    
    print("\nApplication Ready!")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)