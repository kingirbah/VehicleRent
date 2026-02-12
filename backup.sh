#!/bin/bash

# JomSewa V6.0 - Automated Backup Script
# Creates timestamped backups of database and uploaded files

# Configuration
BACKUP_DIR="backups"
DB_FILE="database.db"
UPLOAD_DIR="static/uploads"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "============================================================"
echo "  🏍️  JomSewa Backup - $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if database exists
if [ ! -f "$DB_FILE" ]; then
    echo -e "${RED}✗ Error: Database file not found!${NC}"
    exit 1
fi

# Backup database
echo "📊 Backing up database..."
DB_BACKUP="$BACKUP_DIR/database_$DATE.db"
cp "$DB_FILE" "$DB_BACKUP"

if [ $? -eq 0 ]; then
    DB_SIZE=$(du -h "$DB_BACKUP" | cut -f1)
    echo -e "${GREEN}✓ Database backed up: $DB_BACKUP ($DB_SIZE)${NC}"
else
    echo -e "${RED}✗ Database backup failed!${NC}"
    exit 1
fi

# Backup uploads directory
if [ -d "$UPLOAD_DIR" ]; then
    echo "📸 Backing up uploaded files..."
    UPLOAD_BACKUP="$BACKUP_DIR/uploads_$DATE.tar.gz"
    tar -czf "$UPLOAD_BACKUP" "$UPLOAD_DIR" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        UPLOAD_SIZE=$(du -h "$UPLOAD_BACKUP" | cut -f1)
        echo -e "${GREEN}✓ Uploads backed up: $UPLOAD_BACKUP ($UPLOAD_SIZE)${NC}"
    else
        echo -e "${YELLOW}⚠ Uploads backup completed with warnings${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Upload directory not found, skipping${NC}"
fi

# Clean up old backups
echo ""
echo "🧹 Cleaning up old backups (older than $RETENTION_DAYS days)..."

# Count files before cleanup
OLD_DB_COUNT=$(find "$BACKUP_DIR" -name "database_*.db" -mtime +$RETENTION_DAYS 2>/dev/null | wc -l)
OLD_UPLOAD_COUNT=$(find "$BACKUP_DIR" -name "uploads_*.tar.gz" -mtime +$RETENTION_DAYS 2>/dev/null | wc -l)

# Delete old database backups
find "$BACKUP_DIR" -name "database_*.db" -mtime +$RETENTION_DAYS -delete 2>/dev/null

# Delete old upload backups
find "$BACKUP_DIR" -name "uploads_*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null

if [ $OLD_DB_COUNT -gt 0 ] || [ $OLD_UPLOAD_COUNT -gt 0 ]; then
    echo -e "${GREEN}✓ Removed $OLD_DB_COUNT old database backups${NC}"
    echo -e "${GREEN}✓ Removed $OLD_UPLOAD_COUNT old upload backups${NC}"
else
    echo "  No old backups to remove"
fi

# Display backup statistics
echo ""
echo "============================================================"
echo "  📊 Backup Statistics"
echo "============================================================"

TOTAL_DB_BACKUPS=$(find "$BACKUP_DIR" -name "database_*.db" 2>/dev/null | wc -l)
TOTAL_UPLOAD_BACKUPS=$(find "$BACKUP_DIR" -name "uploads_*.tar.gz" 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)

echo "Database backups: $TOTAL_DB_BACKUPS files"
echo "Upload backups: $TOTAL_UPLOAD_BACKUPS files"
echo "Total backup size: $TOTAL_SIZE"
echo ""

# List recent backups
echo "Recent backups:"
echo "---"
find "$BACKUP_DIR" -name "database_*.db" -o -name "uploads_*.tar.gz" | sort -r | head -n 5 | while read file; do
    SIZE=$(du -h "$file" | cut -f1)
    echo "  $(basename $file) - $SIZE"
done

echo ""
echo "============================================================"
echo -e "  ${GREEN}✅ Backup Complete!${NC}"
echo "============================================================"
echo ""

# Return success
exit 0
