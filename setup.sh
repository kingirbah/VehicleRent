#!/bin/bash

# JomSewa V6.0 - Quick Setup Script
# Automates the installation and initial setup

echo ""
echo "============================================================"
echo "  🏍️  JomSewa Motorcycle Rental V6.0 - Quick Setup"
echo "============================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "📌 Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
    echo -e "${GREEN}   ✓ Python $PYTHON_VERSION detected${NC}"
else
    echo -e "${RED}   ✗ Python 3 not found!${NC}"
    echo "   Please install Python 3.8 or higher"
    exit 1
fi

# Check if running in virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}   ✓ Virtual environment active${NC}"
else
    echo -e "${YELLOW}   ⚠ Not in virtual environment${NC}"
    echo ""
    read -p "   Create virtual environment? (recommended) (y/n): " create_venv
    
    if [ "$create_venv" = "y" ]; then
        echo "   Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        echo -e "${GREEN}   ✓ Virtual environment created and activated${NC}"
    fi
fi

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ Dependencies installed successfully${NC}"
else
    echo -e "${RED}   ✗ Failed to install dependencies${NC}"
    exit 1
fi

# Create necessary directories
echo ""
echo "📁 Creating directory structure..."
mkdir -p static/uploads/vehicles
mkdir -p templates
touch static/uploads/vehicles/.gitkeep

echo -e "${GREEN}   ✓ Directories created${NC}"

# Check if database exists
echo ""
if [ -f "database.db" ]; then
    echo -e "${YELLOW}⚠️  Existing database detected${NC}"
    echo ""
    read -p "   Run database migration? (y/n): " run_migration
    
    if [ "$run_migration" = "y" ]; then
        # Backup first
        BACKUP_NAME="database.db.backup_$(date +%Y%m%d_%H%M%S)"
        cp database.db "$BACKUP_NAME"
        echo -e "${GREEN}   ✓ Backup created: $BACKUP_NAME${NC}"
        
        # Run migration
        echo ""
        echo "🔄 Running database migration..."
        python migrate_database.py
    fi
else
    echo "📊 No existing database found"
    echo "   Database will be created automatically on first run"
fi

# Configuration reminder
echo ""
echo "============================================================"
echo "  ⚙️  IMPORTANT: Configuration Required"
echo "============================================================"
echo ""
echo "Before running in production, update these settings in app.py:"
echo ""
echo "1. Change admin password (line 16):"
echo "   ADMIN_PASSWORD = \"your_secure_password_here\""
echo ""
echo "2. Update WhatsApp number (line 17):"
echo "   WHATSAPP_NUMBER = \"60123456789\""
echo ""
echo "3. Generate and set secret key (line 13):"
echo "   Run: python -c \"import secrets; print(secrets.token_hex(32))\""
echo ""

# Completion
echo "============================================================"
echo "  ✅ Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Review configuration in app.py"
echo "2. Start the application:"
echo "   python app.py"
echo ""
echo "3. Access admin panel:"
echo "   http://localhost:5000/login"
echo "   Default password: admin123"
echo ""
echo "4. For production deployment, see:"
echo "   DEPLOYMENT_GUIDE.md"
echo ""
echo "============================================================"
echo ""

# Ask if user wants to start the app now
read -p "Start the application now? (y/n): " start_now

if [ "$start_now" = "y" ]; then
    echo ""
    echo "🚀 Starting JomSewa application..."
    echo ""
    python app.py
fi
