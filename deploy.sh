#!/bin/bash
# Professional deployment script for ERPNext Telegram Bot
# Author: Claude Code
# Usage: ./deploy.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "======================================"
echo "  ERPNext Telegram Bot Deployment"
echo "======================================"
echo -e "${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ============================================================================
# 1. BACKUP (optional but recommended)
# ============================================================================
echo -e "${YELLOW}[1/9] Creating backup...${NC}"
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/.env.backup"
    echo -e "${GREEN}✅ .env backed up${NC}"
fi

# ============================================================================
# 2. STOP RUNNING BOT
# ============================================================================
echo -e "${YELLOW}[2/9] Stopping running bot...${NC}"
pkill -9 -f "uvicorn.*erpnext_bot" 2>/dev/null || true
pkill -9 -f "python.*app.webhook" 2>/dev/null || true
sleep 2
echo -e "${GREEN}✅ Old processes stopped${NC}"

# ============================================================================
# 3. CLEAN PYTHON CACHE (IMPORTANT!)
# ============================================================================
echo -e "${YELLOW}[3/9] Cleaning Python cache...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo -e "${GREEN}✅ Python cache cleaned${NC}"

# ============================================================================
# 4. GIT PULL
# ============================================================================
echo -e "${YELLOW}[4/9] Pulling latest code from Git...${NC}"
git fetch origin
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"

# Show changes
echo "Recent commits:"
git log origin/$CURRENT_BRANCH --oneline -3

# Pull changes
git pull origin $CURRENT_BRANCH

# Show what changed
echo "Files changed:"
git diff --name-only HEAD@{1} HEAD | head -10
echo -e "${GREEN}✅ Code updated${NC}"

# ============================================================================
# 5. CHECK/UPDATE .env FILE
# ============================================================================
echo -e "${YELLOW}[5/9] Checking .env file...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env with your credentials!${NC}"
    exit 1
fi

# Check if SUPPORT fields exist
if ! grep -q "SUPPORT_PHONE" .env; then
    echo -e "${YELLOW}Adding SUPPORT configuration to .env...${NC}"
    echo "" >> .env
    echo "# Support Configuration" >> .env
    echo "SUPPORT_PHONE=+998 99 123 45 67" >> .env
    echo "SUPPORT_NAME=Operator" >> .env
    echo -e "${GREEN}✅ SUPPORT config added${NC}"
fi

echo -e "${GREEN}✅ .env file OK${NC}"

# ============================================================================
# 6. VIRTUAL ENVIRONMENT CHECK
# ============================================================================
echo -e "${YELLOW}[6/9] Checking virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# ============================================================================
# 7. INSTALL/UPDATE DEPENDENCIES
# ============================================================================
echo -e "${YELLOW}[7/9] Checking dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    .venv/bin/pip install --upgrade pip -q
    .venv/bin/pip install -r requirements.txt -q
    echo -e "${GREEN}✅ Dependencies up to date${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt not found, skipping...${NC}"
fi

# ============================================================================
# 8. TEST IMPORTS
# ============================================================================
echo -e "${YELLOW}[8/9] Testing critical imports...${NC}"
.venv/bin/python -B -c "
import sys
sys.dont_write_bytecode = True
try:
    from app.config import config
    from app.services.support import get_support_contact_sync
    from app.handlers.passport import passport_input_handler
    from app.webhook.server import app
    contact = get_support_contact_sync()
    print(f'✅ All imports OK')
    print(f'✅ Support contact: {contact[\"name\"]} - {contact[\"phone\"]}')
except Exception as e:
    print(f'❌ Import test failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" || {
    echo -e "${RED}❌ Import test failed! Check errors above.${NC}"
    exit 1
}

# ============================================================================
# 9. START BOT
# ============================================================================
echo -e "${YELLOW}[9/9] Starting bot...${NC}"

# Check if port is in use
if lsof -ti:8001 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port 8001 is in use, cleaning...${NC}"
    kill -9 $(lsof -ti:8001) 2>/dev/null || true
    sleep 2
fi

# Start bot with proper flags
PYTHONDONTWRITEBYTECODE=1 nohup .venv/bin/python -B -m uvicorn app.webhook.server:app \
  --host 0.0.0.0 \
  --port 8001 \
  --reload \
  > bot.log 2>&1 &

BOT_PID=$!
echo -e "${GREEN}✅ Bot started with PID: $BOT_PID${NC}"

# Wait for bot to start
echo "Waiting for bot to start..."
sleep 5

# Check if bot is running
if ps -p $BOT_PID > /dev/null; then
    echo -e "${GREEN}✅ Bot is running!${NC}"
else
    echo -e "${RED}❌ Bot failed to start!${NC}"
    echo "Last 20 lines of log:"
    tail -20 bot.log
    exit 1
fi

# Show recent logs
echo ""
echo -e "${BLUE}======================================"
echo "  DEPLOYMENT SUCCESSFUL!"
echo "======================================${NC}"
echo ""
echo -e "${GREEN}📊 Bot Status:${NC}"
echo "   PID: $BOT_PID"
echo "   Port: 8001"
echo "   Log: tail -f bot.log"
echo ""
echo -e "${GREEN}🔍 Useful Commands:${NC}"
echo "   View logs: tail -f bot.log"
echo "   Check process: ps aux | grep uvicorn"
echo "   Stop bot: pkill -f uvicorn"
echo "   Restart: ./deploy.sh"
echo ""
echo -e "${YELLOW}📋 Recent Logs:${NC}"
echo "--------------------------------------"
tail -15 bot.log
echo "--------------------------------------"
echo ""
echo -e "${GREEN}✅ Deployment complete! Test the bot on Telegram.${NC}"
echo ""
