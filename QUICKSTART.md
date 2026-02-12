# ⚡ JomSewa V6.0 - Quick Start Guide

## 🚀 Get Running in 3 Minutes

### Step 1: Install (30 seconds)
```bash
# Option A: Auto setup (recommended)
bash setup.sh

# Option B: Manual setup
pip install -r requirements.txt
```

### Step 2: Run (10 seconds)
```bash
python app.py
```

### Step 3: Login (5 seconds)
1. Open: http://localhost:5000/login
2. Password: `admin123`
3. You're in! 🎉

---

## 📝 First Things to Do

### 1. Change Password ⚠️
Edit `app.py` line 16:
```python
ADMIN_PASSWORD = "your_secure_password"
```

### 2. Add Your First Vehicle
1. Go to `/admin`
2. Click "+ Add New Vehicle"
3. Fill in details:
   - Name (e.g., "Honda Beat")
   - Type (e.g., "Scooter")
   - CC (e.g., "110")
   - License Plate (e.g., "WXY 1234") - NEW!
   - Prices
   - Upload image directly! - NEW!

### 3. Create First Booking
1. Click on vehicle
2. Click "+ New Booking"
3. Fill customer details
4. Booking number auto-generates! (e.g., JS-20260206-0001)
5. Done! ✅

---

## 🆕 What's New in V6.0?

### ✨ 5 Major Features

1. **License Plates** 🚗
   - Track vehicle registration
   - Shows on all vehicle cards

2. **Image Upload** 📸
   - Upload images directly
   - Auto-compresses to < 1MB
   - No external hosting needed

3. **All Bookings View** 📊
   - See ALL bookings in one place
   - Advanced filters & search
   - Real-time statistics
   - Route: `/admin/bookings`

4. **Customer Nationality** 🌍
   - Track where customers are from
   - Searchable field
   - Default: "Malaysian"

5. **Performance** ⚡
   - 10x faster queries
   - Database indexes
   - Optimized search

---

## 🎯 Key Routes

| Route | What It Does |
|-------|-------------|
| `/` | Public catalog (customer view) |
| `/login` | Admin login |
| `/admin` | Vehicle catalog (admin) |
| `/admin/vehicle/add` | Add new vehicle |
| `/admin/bookings` | **NEW!** All bookings |
| `/admin/bookings/print` | **NEW!** Print report |

---

## 🔍 Quick Tips

### Adding Vehicles
- Upload images directly from computer
- License plate is optional but recommended
- System auto-compresses large images

### Managing Bookings
- Booking numbers auto-generate
- Format: JS-YYYYMMDD-XXXX
- Use "All Bookings" for complete overview

### Using Filters
1. Go to `/admin/bookings`
2. Select status, vehicle, or search
3. Click "Apply Filters"
4. Export with "Print Report"

### Search Tips
Search works across:
- Booking numbers
- Customer names
- IC numbers
- Vehicle names
- License plates
- Nationality

---

## 📱 WhatsApp Integration

Update your number in `app.py` line 17:
```python
WHATSAPP_NUMBER = "60123456789"
```

Customers can contact you via WhatsApp button in catalog.

---

## 💾 Quick Backup

```bash
# Backup database
cp database.db database.db.backup

# Backup images
tar -czf uploads_backup.tar.gz static/uploads/
```

---

## 🐛 Quick Fixes

### App won't start
```bash
pip install -r requirements.txt
```

### Images not uploading
```bash
chmod -R 755 static/uploads/
```

### Database error
```bash
python migrate_database.py
```

### Reset everything
```bash
rm database.db
python app.py
```

---

## 📊 Understanding Booking Numbers

Format: **JS-YYYYMMDD-XXXX**

Example: **JS-20260206-0001**
- `JS` = JomSewa
- `20260206` = February 6, 2026
- `0001` = First booking of the day

Benefits:
- ✅ Unique identifier
- ✅ Date-based
- ✅ Professional
- ✅ Easy to reference

---

## 🎨 Customization Quick Guide

### Change Colors
Edit templates, look for:
- `bg-blue-600` → Primary color
- `text-blue-600` → Text color
- `border-blue-500` → Border color

### Add Fields
1. Update database (see IMPLEMENTATION_GUIDE.md)
2. Update templates
3. Update routes in app.py

### Change Logo
Replace "🏍️" with your logo in templates

---

## 📈 Next Steps

### For Development
1. ✅ Install and test locally
2. ✅ Add sample vehicles
3. ✅ Create test bookings
4. ✅ Explore all features

### For Production
1. Change admin password
2. Generate secret key
3. Set up HTTPS
4. Configure backups
5. See DEPLOYMENT_GUIDE.md

---

## 🆘 Need Help?

### Documentation
- **README.md** - Full overview
- **IMPLEMENTATION_GUIDE.md** - Detailed features
- **DEPLOYMENT_GUIDE.md** - Production setup
- **TEMPLATE_UPDATE_GUIDE.md** - HTML customization

### Quick Links
- Check logs in terminal
- Test in development first
- Backup before changes
- Read error messages carefully

---

## ✅ Checklist

Setup complete when you can:
- [ ] Login to admin panel
- [ ] Add a vehicle with license plate
- [ ] Upload an image
- [ ] Create a booking
- [ ] See booking number generated
- [ ] Access `/admin/bookings`
- [ ] Use filters and search
- [ ] Print a report

---

## 🎉 You're Ready!

**Start building your rental empire! 🏍️**

Questions? Check the guides or test locally first.

Happy renting! ✨

---

Last Updated: February 6, 2026  
Version: 6.0 Complete
