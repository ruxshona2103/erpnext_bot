#!/bin/bash

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
echo "  PRODUCTION MODE"
echo "======================================"
echo -e "${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ============================================================================
# 1. BACKUP
# ============================================================================
echo -e "${YELLOW}[1/11] Creating backup...${NC}"
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/.env.backup"
    echo -e "${GREEN}✅ .env backed up${NC}"
fi

# ============================================================================
# 2. STOP RUNNING BOT
# ============================================================================
echo -e "${YELLOW}[2/11] Stopping running bot...${NC}"
pkill -9 -f "uvicorn.*erpnext_bot" 2>/dev/null || true
pkill -9 -f "uvicorn.*app.webhook" 2>/dev/null || true
pkill -9 -f "python.*app.webhook" 2>/dev/null || true
pkill -9 -f "python.*bot" 2>/dev/null || true
sleep 3
echo -e "${GREEN}✅ Old processes stopped${NC}"

# ============================================================================
# 3. CLEAN PYTHON CACHE
# ============================================================================
echo -e "${YELLOW}[3/11] Cleaning Python cache...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo -e "${GREEN}✅ Python cache cleaned${NC}"

# ============================================================================
# 4. GIT PULL
# ============================================================================
echo -e "${YELLOW}[4/11] Pulling latest code from Git...${NC}"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo -e "${YELLOW}⚠️  You have uncommitted changes!${NC}"
    git status --short
    read -p "Stash changes and continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git stash push -m "Auto-stash before deploy $(date +%Y%m%d_%H%M%S)"
        echo -e "${GREEN}✅ Changes stashed${NC}"
    else
        echo -e "${RED}❌ Deploy cancelled${NC}"
        exit 1
    fi
fi

git fetch origin
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"

# Check if pull will cause conflicts
git pull origin $CURRENT_BRANCH || {
    echo -e "${RED}❌ Git pull failed! Please resolve conflicts manually.${NC}"
    exit 1
}

echo -e "${GREEN}✅ Code updated${NC}"

# ============================================================================
# 5. LOAD AND VALIDATE .env
# ============================================================================
echo -e "${YELLOW}[5/11] Validating .env configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    exit 1
fi

# Source .env to get variables
set -a
source .env
set +a

# Validate critical variables
if [ -z "$BOT_TOKEN" ]; then
    echo -e "${RED}❌ BOT_TOKEN not set in .env${NC}"
    exit 1
fi

if [ -z "$WEBHOOK_URL" ]; then
    echo -e "${RED}❌ WEBHOOK_URL not set in .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment validated${NC}"
echo "   Bot Token: ${BOT_TOKEN:0:10}..."
echo "   Webhook URL: $WEBHOOK_URL"

# ============================================================================
# 6. DETECT DEPLOYMENT MODE
# ============================================================================
echo -e "${YELLOW}[6/11] Detecting deployment mode...${NC}"

if [[ "$WEBHOOK_URL" == *"ngrok"* ]]; then
    echo -e "${BLUE}📱 NGROK MODE DETECTED${NC}"
    DEPLOYMENT_MODE="ngrok"

    # Check if ngrok is running
    if ! pgrep -x "ngrok" > /dev/null; then
        echo -e "${RED}❌ Ngrok is not running!${NC}"
        echo -e "${YELLOW}Please start ngrok first:${NC}"
        echo "   ngrok http 8001"
        exit 1
    fi

    echo -e "${GREEN}✅ Ngrok is running${NC}"
else
    echo -e "${BLUE}🌐 PRODUCTION MODE (Domain-based)${NC}"
    DEPLOYMENT_MODE="production"
fi

# ============================================================================
# 7. VIRTUAL ENVIRONMENT
# ============================================================================
echo -e "${YELLOW}[7/11] Setting up virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# ============================================================================
# 8. INSTALL DEPENDENCIES
# ============================================================================
echo -e "${YELLOW}[8/11] Installing dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    .venv/bin/pip install --upgrade pip -q
    .venv/bin/pip install -r requirements.txt -q
    echo -e "${GREEN}✅ Dependencies installed${NC}"
fi

# ============================================================================
# 9. DELETE OLD WEBHOOK
# ============================================================================
echo -e "${YELLOW}[9/11] Deleting old webhook...${NC}"
.venv/bin/python -B << 'PYEOF'
import sys
import requests
import os

BOT_TOKEN = os.getenv('BOT_TOKEN')
url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"

try:
    response = requests.post(url, json={"drop_pending_updates": True}, timeout=10)
    if response.status_code == 200:
        print("✅ Old webhook deleted")
    else:
        print(f"⚠️  Webhook delete response: {response.status_code}")
except Exception as e:
    print(f"⚠️  Could not delete webhook: {e}")
PYEOF

sleep 2

# ============================================================================
# 10. START BOT (WITHOUT --reload for production)
# ============================================================================
echo -e "${YELLOW}[10/11] Starting bot server...${NC}"

# Kill any process using port 8001 (fallback methods)
PORT_PID=""
if command -v lsof > /dev/null 2>&1; then
    # Method 1: lsof (most reliable)
    PORT_PID=$(lsof -ti:8001 2>/dev/null || true)
elif command -v ss > /dev/null 2>&1; then
    # Method 2: ss (modern alternative)
    PORT_PID=$(ss -lptn "sport = :8001" 2>/dev/null | grep -oP 'pid=\K\d+' || true)
elif command -v netstat > /dev/null 2>&1; then
    # Method 3: netstat (legacy fallback)
    PORT_PID=$(netstat -tlnp 2>/dev/null | grep ':8001' | awk '{print $7}' | cut -d'/' -f1 || true)
fi

if [ ! -z "$PORT_PID" ]; then
    echo -e "${YELLOW}⚠️  Port 8001 is in use (PID: $PORT_PID), cleaning...${NC}"
    kill -9 $PORT_PID 2>/dev/null || true
    sleep 2
fi

# Start server based on mode
if [ "$DEPLOYMENT_MODE" = "production" ]; then
    echo -e "${BLUE}Starting in PRODUCTION mode (4 workers, no reload)...${NC}"
    PYTHONDONTWRITEBYTECODE=1 nohup .venv/bin/python -B -m uvicorn app.webhook.server:app \
      --host 0.0.0.0 \
      --port 8001 \
      --workers 4 \
      > bot.log 2>&1 &
else
    echo -e "${BLUE}Starting in DEVELOPMENT mode (reload enabled)...${NC}"
    PYTHONDONTWRITEBYTECODE=1 nohup .venv/bin/python -B -m uvicorn app.webhook.server:app \
      --host 0.0.0.0 \
      --port 8001 \
      --reload \
      > bot.log 2>&1 &
fi

BOT_PID=$!
echo -e "${GREEN}✅ Bot started with PID: $BOT_PID${NC}"

# Wait for server to start (multiple checks)
echo "Waiting for server to start..."
SERVER_READY=false

for i in {1..15}; do
    # Method 1: Try /health endpoint if it exists
    if curl -s http://127.0.0.1:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Server is responding (health check passed)${NC}"
        SERVER_READY=true
        break
    fi

    # Method 2: Check if port is listening
    if command -v nc > /dev/null 2>&1; then
        if nc -z 127.0.0.1 8001 2>/dev/null; then
            echo -e "${GREEN}✅ Server is listening on port 8001${NC}"
            SERVER_READY=true
            break
        fi
    fi

    # Method 3: Check if process is still alive
    if ! ps -p $BOT_PID > /dev/null 2>&1; then
        echo -e "${RED}❌ Bot process died!${NC}"
        echo "Last 50 lines of log:"
        tail -50 bot.log
        exit 1
    fi

    sleep 1
done

if [ "$SERVER_READY" = false ]; then
    echo -e "${YELLOW}⚠️  Server health check failed, but process is running${NC}"
    echo -e "${YELLOW}Waiting 3 more seconds...${NC}"
    sleep 3

    # Final check: if process alive, assume OK
    if ps -p $BOT_PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Bot process is running (PID: $BOT_PID)${NC}"
    else
        echo -e "${RED}❌ Bot failed to start!${NC}"
        echo "Last 50 lines of log:"
        tail -50 bot.log
        exit 1
    fi
fi

# ============================================================================
# 11. SET WEBHOOK
# ============================================================================
echo -e "${YELLOW}[11/11] Setting webhook...${NC}"

.venv/bin/python -B << 'PYEOF'
import sys
import requests
import os
import time

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/webhook')

full_webhook_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"

print(f"Setting webhook to: {full_webhook_url}")

# Wait a bit more for server
time.sleep(3)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
data = {
    "url": full_webhook_url,
    "drop_pending_updates": True,
    "allowed_updates": ["message", "callback_query"]
}

try:
    response = requests.post(url, json=data, timeout=15)
    result = response.json()

    if result.get("ok"):
        print("✅ Webhook set successfully!")
        print(f"   URL: {full_webhook_url}")
    else:
        print(f"❌ Webhook set failed: {result.get('description', 'Unknown error')}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error setting webhook: {e}")
    sys.exit(1)

# Verify webhook
time.sleep(1)
verify_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
try:
    response = requests.get(verify_url, timeout=10)
    info = response.json()

    if info.get("ok"):
        webhook_info = info.get("result", {})
        print("\n📊 Webhook Info:")
        print(f"   URL: {webhook_info.get('url', 'Not set')}")
        print(f"   Pending updates: {webhook_info.get('pending_update_count', 0)}")
        if webhook_info.get('last_error_message'):
            print(f"   ⚠️  Last error: {webhook_info.get('last_error_message')}")
            print(f"   Last error date: {webhook_info.get('last_error_date', 'Unknown')}")
except Exception as e:
    print(f"⚠️  Could not verify webhook: {e}")
PYEOF

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Webhook setup failed!${NC}"
    exit 1
fi

# ============================================================================
# DEPLOYMENT COMPLETE
# ============================================================================
echo ""
echo -e "${BLUE}======================================"
echo "  ✅ DEPLOYMENT SUCCESSFUL!"
echo "======================================${NC}"
echo ""
echo -e "${GREEN}📊 Bot Status:${NC}"
echo "   Mode: $DEPLOYMENT_MODE"
echo "   PID: $BOT_PID"
echo "   Port: 8001"
echo "   Webhook: $WEBHOOK_URL$WEBHOOK_PATH"
echo ""
echo -e "${GREEN}🔍 Useful Commands:${NC}"
echo "   View logs:       tail -f bot.log"
echo "   Check webhook:   curl https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo"
echo "   Test locally:    curl http://127.0.0.1:8001/webhook"
echo "   Check process:   ps aux | grep $BOT_PID"
echo "   Stop bot:        kill $BOT_PID  (or: pkill -f uvicorn)"
echo "   Restart:         ./deploy.sh"
echo ""

if [ "$DEPLOYMENT_MODE" = "ngrok" ]; then
    echo -e "${YELLOW}⚠️  NGROK MODE WARNINGS:${NC}"
    echo "   • Don't close ngrok terminal"
    echo "   • URL changes when ngrok restarts"
    echo "   • Not suitable for production"
    echo ""
fi

echo -e "${YELLOW}📋 Recent Logs:${NC}"
echo "--------------------------------------"
tail -20 bot.log
echo "--------------------------------------"
echo ""
echo -e "${GREEN}✅ Bot is ready! Send /start to test.${NC}"
echo ""