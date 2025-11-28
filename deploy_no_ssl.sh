#!/bin/bash

# ============================================================================
# DEPLOY WITHOUT SSL - For Testing / DNS Issues
# Use this if SSL fails, then add SSL later
# ============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear

echo -e "${BLUE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   BOT DEPLOYMENT (NO SSL - HTTP ONLY)"
echo "   For testing or if DNS not ready"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Load .env
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    exit 1
fi

source .env 2>/dev/null || export $(cat .env | grep -v '^#' | xargs)

DOMAIN=$(echo $WEBHOOK_URL | sed -e 's|^[^/]*//||' -e 's|/.*$||')
BOT_PORT=${PORT:-8001}
SERVER_IP=$(curl -s ifconfig.me)

echo -e "${YELLOW}⚠️  WARNING: This will deploy bot WITHOUT SSL${NC}"
echo -e "${YELLOW}⚠️  Telegram webhooks require HTTPS in production${NC}"
echo -e "${YELLOW}⚠️  This is for testing only!${NC}"
echo ""
echo "Configuration:"
echo "   Domain:    $DOMAIN"
echo "   Server IP: $SERVER_IP"
echo "   Port:      $BOT_PORT"
echo ""
read -p "Continue without SSL? (y/N): " -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# ============================================================================
# STOP OLD BOT
# ============================================================================
echo -e "${YELLOW}[1/4] Stopping old bot...${NC}"

pkill -9 -f "uvicorn.*erpnext_bot" 2>/dev/null || true
if lsof -ti:${BOT_PORT} > /dev/null 2>&1; then
    kill -9 $(lsof -ti:${BOT_PORT}) 2>/dev/null || true
fi
sleep 2

echo -e "${GREEN}✅ Old processes stopped${NC}"
echo ""

# ============================================================================
# CLEAN CACHE
# ============================================================================
echo -e "${YELLOW}[2/4] Cleaning cache...${NC}"

find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo -e "${GREEN}✅ Cache cleaned${NC}"
echo ""

# ============================================================================
# INSTALL DEPENDENCIES
# ============================================================================
echo -e "${YELLOW}[3/4] Installing dependencies...${NC}"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# ============================================================================
# START BOT
# ============================================================================
echo -e "${YELLOW}[4/4] Starting bot...${NC}"

PYTHONDONTWRITEBYTECODE=1 nohup .venv/bin/python -B -m uvicorn app.webhook.server:app \
  --host 0.0.0.0 \
  --port ${BOT_PORT} \
  --log-level info \
  > bot.log 2>&1 &

BOT_PID=$!
echo $BOT_PID > bot.pid

echo -e "${GREEN}✅ Bot started (PID: ${BOT_PID})${NC}"
echo ""

sleep 5

if ! ps -p $BOT_PID > /dev/null 2>&1; then
    echo -e "${RED}❌ Bot failed to start${NC}"
    tail -20 bot.log
    exit 1
fi

echo -e "${GREEN}✅ Bot is running${NC}"
echo ""

# ============================================================================
# CHECK WEBHOOK
# ============================================================================
echo -e "${YELLOW}Checking webhook...${NC}"
sleep 3

WEBHOOK_INFO=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo")
echo "$WEBHOOK_INFO" | jq '.' 2>/dev/null || echo "$WEBHOOK_INFO"

echo ""

# ============================================================================
# SUCCESS
# ============================================================================
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   BOT DEPLOYED (NO SSL)${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}Status:${NC}"
echo "   Bot PID: $BOT_PID"
echo "   Port:    $BOT_PORT"
echo ""
echo -e "${CYAN}Logs:${NC}"
echo "   tail -f bot.log"
echo ""
echo -e "${YELLOW}⚠️  Important:${NC}"
echo "   - Bot is running WITHOUT SSL"
echo "   - Webhook may not work (Telegram requires HTTPS)"
echo "   - Fix DNS and run: ./deploy_root.sh"
echo ""
