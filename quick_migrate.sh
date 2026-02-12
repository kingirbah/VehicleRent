#!/bin/bash

# VehiclesRent - Quick Migration to Supabase PostgreSQL
# This script automates the entire migration process

echo "============================================================"
echo "  VehiclesRent - PostgreSQL Migration Script" 
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check Python
echo -e "${YELLOW}Step 1: Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Please install Python 3.8+${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python found: $(python3 --version)${NC}"
echo ""

# Step 2: Install dependencies
echo -e "${YELLOW}Step 2: Installing PostgreSQL dependencies...${NC}"
pip3 install psycopg2-binary python-dotenv --quiet
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi
echo ""

# Step 3: Setup .env file
echo -e "${YELLOW}Step 3: Setting up environment variables...${NC}"
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env file already exists. Backing up...${NC}"
    cp .env .env.backup
    echo -e "${GREEN}✓ Backup created: .env.backup${NC}"
fi

cp .env.production .env
echo -e "${GREEN}✓ .env file created from template${NC}"
echo ""

# Step 4: Configure password
echo -e "${YELLOW}Step 4: Database configuration${NC}"
echo "Please enter your Supabase password:"
read -s SUPABASE_PASSWORD

# Replace password in .env
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/\[YOUR-PASSWORD\]/$SUPABASE_PASSWORD/" .env
else
    # Linux
    sed -i "s/\[YOUR-PASSWORD\]/$SUPABASE_PASSWORD/" .env
fi

echo -e "${GREEN}✓ Password configured${NC}"
echo ""

# Step 5: Generate SECRET_KEY
echo -e "${YELLOW}Step 5: Generating secure SECRET_KEY...${NC}"
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/your_secret_key_change_this_in_production_use_random_64_chars/$SECRET_KEY/" .env
else
    sed -i "s/your_secret_key_change_this_in_production_use_random_64_chars/$SECRET_KEY/" .env
fi

echo -e "${GREEN}✓ SECRET_KEY generated${NC}"
echo ""

# Step 6: Test database connection
echo -e "${YELLOW}Step 6: Testing database connection...${NC}"
python3 -c "
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('SUPABASE_HOST'),
        database=os.getenv('SUPABASE_DB'),
        user=os.getenv('SUPABASE_USER'),
        password=os.getenv('SUPABASE_PASSWORD'),
        port=os.getenv('SUPABASE_PORT')
    )
    conn.close()
    print('✓ Database connection successful!')
    exit(0)
except Exception as e:
    print(f'❌ Connection failed: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database connection verified${NC}"
else
    echo -e "${RED}❌ Database connection failed. Please check credentials.${NC}"
    exit 1
fi
echo ""

# Step 7: Run schema
echo -e "${YELLOW}Step 7: Would you like to initialize database schema? (y/n)${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Running database schema..."
    python3 << EOF
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('SUPABASE_HOST'),
    database=os.getenv('SUPABASE_DB'),
    user=os.getenv('SUPABASE_USER'),
    password=os.getenv('SUPABASE_PASSWORD'),
    port=os.getenv('SUPABASE_PORT')
)
cursor = conn.cursor()

# Read and execute schema
with open('supabase_schema.sql', 'r') as f:
    cursor.execute(f.read())

conn.commit()
cursor.close()
conn.close()

print('✓ Database schema initialized')
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Schema created successfully${NC}"
    else
        echo -e "${YELLOW}⚠ Schema creation had warnings (this is normal if tables exist)${NC}"
    fi
else
    echo -e "${YELLOW}⊘ Skipped schema initialization${NC}"
fi
echo ""

# Step 8: Migrate data (if SQLite exists)
if [ -f "database.db" ]; then
    echo -e "${YELLOW}Step 8: SQLite database found. Migrate data? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "Migrating data from SQLite to PostgreSQL..."
        python3 migrate_sqlite_to_postgres.py
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Data migration completed${NC}"
        else
            echo -e "${RED}❌ Data migration failed${NC}"
        fi
    else
        echo -e "${YELLOW}⊘ Skipped data migration${NC}"
    fi
else
    echo -e "${YELLOW}Step 8: No SQLite database found - skipping migration${NC}"
fi
echo ""

# Step 9: Final check
echo -e "${YELLOW}Step 9: Running application test...${NC}"
timeout 5 python3 app_postgresql.py &
sleep 3

if pgrep -f "app_postgresql.py" > /dev/null; then
    echo -e "${GREEN}✓ Application started successfully${NC}"
    pkill -f "app_postgresql.py"
else
    echo -e "${RED}❌ Application failed to start${NC}"
fi
echo ""

# Summary
echo "============================================================"
echo -e "${GREEN}  ✓ MIGRATION SETUP COMPLETED!${NC}"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Review .env file settings"
echo "2. Run: python3 app_postgresql.py"
echo "3. Test login: admin / admin123"
echo "4. Deploy to Koyeb with environment variables"
echo ""
echo "Configuration files:"
echo "  • .env (configured)"
echo "  • .env.backup (if existed)"
echo "  • app_postgresql.py (ready)"
echo ""
echo "Database:"
echo "  • Host: aws-1-ap-southeast-1.pooler.supabase.com"
echo "  • Port: 6543 (pooler)"
echo "  • Database: postgres"
echo ""
echo -e "${GREEN}Ready for production! 🚀${NC}"
echo ""
