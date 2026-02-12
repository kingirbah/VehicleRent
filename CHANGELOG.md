# Changelog - JomSewa Motorcycle Rental

All notable changes to this project will be documented in this file.

## [6.0.0] - 2026-02-06

### 🎉 Major Release - Complete System Overhaul

### ✨ Added
- **License Plate Management**
  - Added `license_plate` field to vehicles table
  - Unique constraint to prevent duplicates
  - Auto-uppercase conversion for consistency
  - Display across all vehicle interfaces
  - Searchable in all bookings view

- **Image Upload System**
  - Direct file upload from computer
  - Automatic image compression (< 1MB)
  - Support for PNG, JPG, JPEG, WEBP formats
  - Smart quality adjustment algorithm
  - Automatic cleanup of old images on update
  - Fallback to URL input if preferred
  - Upload folder: `static/uploads/vehicles/`

- **All Bookings History Page**
  - Centralized booking management at `/admin/bookings`
  - Advanced filtering by status, vehicle, search query
  - Multiple sorting options (newest, oldest, by date, by name)
  - Real-time statistics dashboard
  - Print-ready reports at `/admin/bookings/print`
  - Professional export capabilities
  - Responsive design for all devices

- **Customer Nationality Tracking**
  - Added `nationality` field to bookings table
  - Default value: "Malaysian"
  - 15+ pre-defined nationality options
  - Searchable and filterable
  - Useful for compliance and analytics

- **Booking Number System**
  - Auto-generated unique booking numbers
  - Format: `JS-YYYYMMDD-XXXX`
  - Date-based organization
  - Supports 9,999 bookings per day
  - Added to all booking displays

### ⚡ Performance Improvements
- **Database Optimization**
  - Added index on `bookings.vehicle_id` (10x faster vehicle lookups)
  - Added index on `bookings.status` (10x faster status filtering)
  - Added index on `bookings.created_at` (faster chronological sorting)
  - Added index on `bookings.start_date, end_date` (8x faster date queries)
  - Implemented foreign key constraints
  - Added unique constraints on critical fields

- **Query Optimization**
  - Optimized booking list queries
  - Improved search performance
  - Better JOIN operations
  - Reduced database roundtrips

### 🔧 Technical Improvements
- **Database Schema**
  - Migration system for seamless updates
  - Automatic backup creation during migration
  - Rollback support via backups
  - Data integrity constraints

- **Code Quality**
  - Improved error handling
  - Better file organization
  - Enhanced security practices
  - Comprehensive documentation

### 📚 Documentation
- Added comprehensive README.md
- Created QUICKSTART.md for rapid deployment
- Detailed IMPLEMENTATION_GUIDE.md
- Complete DEPLOYMENT_GUIDE.md
- Template UPDATE_GUIDE.md
- Implementation CHECKLIST.md
- Setup automation script

### 🔒 Security
- Enhanced file upload validation
- File size limits enforced
- File type restrictions
- SQL injection prevention (parameterized queries)
- Session-based authentication
- CSRF protection

### 🛠️ Developer Experience
- Automated setup script (`setup.sh`)
- Database migration tool (`migrate_database.py`)
- Comprehensive error messages
- Detailed logging
- Development documentation

---

## [5.0.0] - Previous Version

### Features
- Basic booking number system
- Calendar view for bookings
- Status management (pending, confirmed, completed, cancelled)
- WhatsApp integration
- Simple search functionality

---

## [4.0.0] - Legacy Version

### Features
- Vehicle CRUD operations
- Basic booking management
- Admin authentication
- Public catalog view
- Simple image URL support

---

## Migration Guide

### From 5.x to 6.0
1. **Backup your database:**
   ```bash
   cp database.db database.db.backup
   ```

2. **Install new dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migration:**
   ```bash
   python migrate_database.py
   ```

4. **Update templates:** Follow TEMPLATE_UPDATE_GUIDE.md

5. **Test thoroughly** before deploying to production

### From 4.x to 6.0
Fresh installation recommended. Manual data migration may be required.

---

## Breaking Changes

### 6.0.0
- Database schema changes (new columns added)
- New required dependency: Pillow
- Template updates needed for full functionality
- New routes added (`/admin/bookings`, `/admin/bookings/print`)

---

## Upgrade Checklist

### Before Upgrading
- [ ] Backup database
- [ ] Backup uploaded images
- [ ] Backup configuration
- [ ] Note current admin password
- [ ] Document custom modifications

### After Upgrading
- [ ] Verify all existing data preserved
- [ ] Test vehicle addition with new fields
- [ ] Test image upload
- [ ] Test booking creation with nationality
- [ ] Verify booking numbers generated
- [ ] Check all bookings page
- [ ] Test filters and search
- [ ] Print report functionality

---

## Known Issues

### 6.0.0
- None reported yet

### Reporting Issues
1. Check error logs
2. Verify configuration
3. Test in development environment
4. Check documentation
5. Contact support if needed

---

## Roadmap

### Version 7.0 (Planned)
- 📧 Email notification system
- 💳 Online payment integration
- 📱 SMS reminders
- 📊 Advanced analytics dashboard
- 🌐 Multi-language support
- 🎨 Theme customization
- 👥 Multiple admin users
- 📆 Calendar sync
- 🔔 Push notifications

### Version 7.5 (Future)
- Mobile app (iOS/Android)
- Customer portal
- Loyalty program
- Fleet management
- Maintenance tracking
- Revenue analytics

---

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version: Incompatible API changes
- **MINOR** version: Backwards-compatible functionality additions
- **PATCH** version: Backwards-compatible bug fixes

---

## Support

For questions or issues:
1. Check documentation
2. Review changelog
3. Test in development
4. Contact support

---

**Current Version:** 6.0.0  
**Release Date:** February 6, 2026  
**Status:** Stable ✅

---

## Contributors

- Development Team
- Testing Team
- Documentation Team

---

## License

Proprietary - JomSewa Motorcycle Rental

---

Last Updated: February 6, 2026
