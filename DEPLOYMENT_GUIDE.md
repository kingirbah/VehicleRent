# 🚀 JomSewa Motorcycle Rental - Complete Deployment Guide

## 📋 Table of Contents
1. [New Features](#new-features)
2. [System Requirements](#system-requirements)
3. [Installation Steps](#installation-steps)
4. [Database Migration](#database-migration)
5. [Configuration](#configuration)
6. [Deployment to Production](#deployment-to-production)
7. [Backup Strategy](#backup-strategy)
8. [Troubleshooting](#troubleshooting)

---

## 🆕 New Features

### 1. **License Plate Management** 🚗
- Added `license_plate` field to vehicles table
- Unique constraint to prevent duplicate plates
- Auto-uppercase conversion for consistency
- Display on all vehicle cards and detail pages

### 2. **Image Upload System** 📸
- Upload images directly from your computer
- Maximum file size: 1MB
- Automatic compression and optimization
- Supported formats: PNG, JPG, JPEG, WEBP
- Falls back to URL input if preferred
- Automatic cleanup of old images when updating

### 3. **All Bookings History** 📊
- Centralized view of ALL bookings across all vehicles
- Advanced filtering:
  - By status (All, Confirmed, Pending, Cancelled, Completed)
  - By vehicle
  - By search query (booking number, customer name, IC, nationality, vehicle)
- Smart sorting:
  - Newest first (default)
  - Oldest first
  - By rental start date
  - By customer name
- Real-time statistics dashboard
- Print-ready reports
- Accessible via `/admin/bookings`

### 4. **Customer Nationality Field** 🌍
- Added `nationality` field to bookings
- Default: "Malaysian"
- Searchable and filterable
- Helps track international customers
- Useful for insurance and compliance

### 5. **Enhanced Database Structure** 🗄️
- Optimized indexes for better performance
- Automatic schema migration
- Foreign key constraints
- Unique constraints on critical fields
- Better data integrity

---

## 💻 System Requirements

### Minimum Requirements:
- **Python**: 3.8 or higher
- **RAM**: 512MB minimum (1GB recommended)
- **Storage**: 1GB free space
- **OS**: Linux, Windows, or macOS

### For Production:
- **Python**: 3.10+
- **RAM**: 2GB+
- **Storage**: 5GB+ (for images and database)
- **Server**: VPS or dedicated server
- **Domain**: Optional but recommended
- **SSL Certificate**: Highly recommended (Let's Encrypt)

---

## 📦 Installation Steps

### Step 1: Clone/Download Files
```bash
# If using git
git clone <your-repo-url>
cd jomsewa-rental

# Or extract from zip
unzip jomsewa-rental.zip
cd jomsewa-rental
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

**requirements.txt content:**
```
Flask==3.0.0
Werkzeug==3.0.1
Pillow==10.1.0
```

### Step 4: Initial Setup
```bash
# The app will auto-create database on first run
python app.py
```

You should see:
```
=============================================================
🚀 INITIALIZING NEW DATABASE
=============================================================
✓ Database initialized successfully!

=============================================================
✓ Application Ready!
=============================================================
📁 Upload folder: static/uploads/vehicles
📏 Max file size: 1.0MB
🔐 Admin password: admin123
=============================================================

 * Running on http://0.0.0.0:5000
```

### Step 5: Access the Application
- **Public Catalog**: http://localhost:5000/
- **Admin Login**: http://localhost:5000/login
- **Default Password**: admin123 (CHANGE THIS!)

---

## 🔄 Database Migration

### If You Have Existing Database

The application includes **automatic migration** that runs on startup. It will:

1. ✅ Add `license_plate` column to vehicles
2. ✅ Add `booking_number` column to bookings
3. ✅ Add `nationality` column to bookings
4. ✅ Generate booking numbers for existing records
5. ✅ Create performance indexes
6. ✅ No data loss - completely safe!

### Manual Migration (Optional)

If you want to run migration separately:

```bash
python migrate_database.py
```

### Backup Before Migration
```bash
# Always backup first!
cp database.db database.db.backup_$(date +%Y%m%d_%H%M%S)
```

### Verify Migration Success
```python
import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Check vehicles table
cursor.execute("PRAGMA table_info(vehicles)")
print("Vehicles columns:", [col[1] for col in cursor.fetchall()])

# Check bookings table
cursor.execute("PRAGMA table_info(bookings)")
print("Bookings columns:", [col[1] for col in cursor.fetchall()])

conn.close()
```

Expected output should include:
- Vehicles: `license_plate`
- Bookings: `booking_number`, `nationality`

---

## ⚙️ Configuration

### 1. Change Admin Password
**File**: `app.py`
```python
# Line 15
ADMIN_PASSWORD = "your_super_secure_password_here"
```

### 2. Update WhatsApp Number
```python
# Line 16
WHATSAPP_NUMBER = "60123456789"  # Your actual number
```

### 3. Adjust Upload Settings
```python
# Line 21-22
MAX_FILE_SIZE = 1 * 1024 * 1024  # Change to 2MB: 2 * 1024 * 1024
```

### 4. Configure Secret Key
```python
# Line 10 - VERY IMPORTANT for production!
app.secret_key = "generate-a-random-secure-key-here"
```

Generate secure key:
```python
import secrets
print(secrets.token_hex(32))
```

---

## 🌐 Deployment to Production

### Option 1: Deploy with Gunicorn (Recommended)

#### Install Gunicorn
```bash
pip install gunicorn
```

#### Create systemd service
**File**: `/etc/systemd/system/jomsewa.service`
```ini
[Unit]
Description=JomSewa Motorcycle Rental
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/jomsewa
Environment="PATH=/var/www/jomsewa/venv/bin"
ExecStart=/var/www/jomsewa/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
```

#### Start service
```bash
sudo systemctl daemon-reload
sudo systemctl start jomsewa
sudo systemctl enable jomsewa
sudo systemctl status jomsewa
```

### Option 2: Deploy with Nginx

#### Install Nginx
```bash
sudo apt install nginx
```

#### Configure Nginx
**File**: `/etc/nginx/sites-available/jomsewa`
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    client_max_body_size 2M;  # Allow file uploads
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /static {
        alias /var/www/jomsewa/static;
        expires 30d;
    }
}
```

#### Enable site
```bash
sudo ln -s /etc/nginx/sites-available/jomsewa /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Option 3: Deploy with SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### Option 4: Deploy to Cloud Platforms

#### DigitalOcean App Platform
1. Create `Procfile`:
   ```
   web: gunicorn app:app
   ```
2. Push to GitHub
3. Connect GitHub repo to DigitalOcean
4. Deploy automatically

#### Heroku
```bash
heroku create jomsewa-rental
git push heroku main
heroku open
```

#### Railway
1. Import from GitHub
2. Add environment variables
3. Deploy automatically

---

## 💾 Backup Strategy

### Automated Daily Backup Script

**File**: `backup.sh`
```bash
#!/bin/bash

# Configuration
BACKUP_DIR="/var/backups/jomsewa"
DB_FILE="database.db"
STATIC_DIR="static/uploads"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
cp $DB_FILE "$BACKUP_DIR/database_$DATE.db"

# Backup images
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" $STATIC_DIR

# Keep only last 30 days
find $BACKUP_DIR -name "database_*.db" -mtime +30 -delete
find $BACKUP_DIR -name "uploads_*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

#### Schedule with Cron
```bash
chmod +x backup.sh

# Edit crontab
crontab -e

# Add this line (daily at 2 AM)
0 2 * * * /path/to/backup.sh >> /var/log/jomsewa_backup.log 2>&1
```

### Cloud Backup

#### Google Drive (using rclone)
```bash
# Install rclone
curl https://rclone.org/install.sh | sudo bash

# Configure Google Drive
rclone config

# Backup script
rclone copy /var/backups/jomsewa gdrive:jomsewa-backups
```

---

## 🐛 Troubleshooting

### Issue: "No module named 'PIL'"
**Solution:**
```bash
pip install Pillow
```

### Issue: "Permission denied" for uploads
**Solution:**
```bash
sudo chown -R www-data:www-data /var/www/jomsewa/static/uploads
sudo chmod -R 755 /var/www/jomsewa/static/uploads
```

### Issue: Images not displaying
**Solution:**
1. Check file permissions
2. Verify path in database starts with `/static/`
3. Check Nginx static file configuration

### Issue: Database locked
**Solution:**
```bash
# Stop all processes
sudo systemctl stop jomsewa

# Check for locks
fuser database.db

# Restart
sudo systemctl start jomsewa
```

### Issue: Booking number generation fails
**Solution:**
```python
# Run this in Python console
from app import get_db, generate_booking_number

db = get_db()
# Check if column exists
cursor = db.cursor()
cursor.execute("PRAGMA table_info(bookings)")
columns = [col[1] for col in cursor.fetchall()]
print("Has booking_number:", 'booking_number' in columns)

# Test generation
print("Generated:", generate_booking_number())
```

### Issue: Migration doesn't run
**Solution:**
```bash
# Delete database and start fresh (BACKUP FIRST!)
cp database.db database.db.backup
rm database.db
python app.py
```

---

## 📊 Database Schema

### Vehicles Table
```sql
CREATE TABLE vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    cc TEXT NOT NULL,
    license_plate TEXT UNIQUE,              -- NEW!
    price_day INTEGER NOT NULL,
    price_3day INTEGER NOT NULL,
    price_weekly INTEGER NOT NULL,
    price_monthly INTEGER NOT NULL,
    image_url TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Bookings Table
```sql
CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_number TEXT UNIQUE NOT NULL,    -- NEW!
    vehicle_id INTEGER NOT NULL,
    customer_name TEXT NOT NULL,
    ic_number TEXT,
    nationality TEXT DEFAULT 'Malaysian',   -- NEW!
    location TEXT,
    destination TEXT,
    start_date TEXT NOT NULL,
    pickup_time TEXT NOT NULL,
    end_date TEXT NOT NULL,
    return_time TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE
);
```

### Indexes
```sql
CREATE INDEX idx_bookings_vehicle ON bookings(vehicle_id);
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_bookings_created ON bookings(created_at);
CREATE INDEX idx_bookings_dates ON bookings(start_date, end_date);
```

---

## 🔒 Security Best Practices

1. **Change default password** immediately
2. **Use HTTPS** in production (SSL certificate)
3. **Set strong secret key** (not the default)
4. **Regular backups** (automated daily)
5. **Update dependencies** regularly
   ```bash
   pip list --outdated
   pip install --upgrade Flask Werkzeug Pillow
   ```
6. **Limit file upload sizes** (already implemented)
7. **Validate file types** (already implemented)
8. **Use environment variables** for sensitive data
9. **Regular security audits**
10. **Monitor logs** for suspicious activity

---

## 📈 Performance Optimization

### 1. Enable SQLite Optimizations
Add to `app.py`:
```python
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    # Optimizations
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('PRAGMA cache_size=10000')
    conn.execute('PRAGMA temp_store=MEMORY')
    return conn
```

### 2. Image Caching
Add to Nginx config:
```nginx
location ~* \.(jpg|jpeg|png|webp)$ {
    expires 365d;
    add_header Cache-Control "public, immutable";
}
```

### 3. Gzip Compression
Add to Nginx config:
```nginx
gzip on;
gzip_types text/css application/javascript image/svg+xml;
gzip_vary on;
```

---

## 📞 Support

For issues or questions:
1. Check this documentation first
2. Review error logs: `/var/log/jomsewa/error.log`
3. Check application logs in console
4. Verify database schema
5. Test in development environment first

---

## 📄 License & Credits

**Application**: JomSewa Motorcycle Rental Management System  
**Version**: 6.0 (2026)  
**Features**: Complete vehicle and booking management with modern UI

---

**Last Updated**: February 6, 2026  
**Status**: Production Ready ✅
