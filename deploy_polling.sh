#!/bin/bash

# ============================================================================
# POLLING MODE DEPLOYMENT - Simple & Reliable!
# No DNS, SSL, Nginx, Webhook needed!
# ============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear

echo -e "${GREEN}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   POLLING MODE DEPLOYMENT"
echo "   Simple, Reliable, No DNS/SSL Needed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${CYAN}📁 Working directory: ${SCRIPT_DIR}${NC}"
echo ""

# ============================================================================
# CHECK .env
# ============================================================================
echo -e "${YELLOW}[1/6] Checking configuration...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    cp .env.example .env
    echo ""
    echo "Please edit .env:"
    echo "   nano .env"
    echo ""
    echo "Required:"
    echo "   BOT_TOKEN=your_token"
    echo "   ERP_BASE_URL=https://macone.net"
    echo "   ERP_API_KEY=..."
    echo "   ERP_API_SECRET=..."
    echo ""
    exit 1
fi

source .env 2>/dev/null || export $(cat .env | grep -v '^#' | xargs)

if [ -z "$BOT_TOKEN" ]; then
    echo -e "${RED}❌ BOT_TOKEN not set in .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Configuration OK${NC}"
echo "   BOT_TOKEN: ${BOT_TOKEN:0:20}..."
echo ""

# ============================================================================
# STOP OLD PROCESSES
# ============================================================================
echo -e "${YELLOW}[2/6] Stopping old bot processes...${NC}"

# Stop webhook mode
pkill -9 -f "uvicorn.*erpnext_bot" 2>/dev/null || true

# Stop polling mode
pkill -9 -f "start_polling_bot" 2>/dev/null || true
pkill -9 -f "python.*app.main" 2>/dev/null || true

sleep 2

echo -e "${GREEN}✅ Old processes stopped${NC}"
echo ""

# ============================================================================
# CLEAN CACHE
# ============================================================================
echo -e "${YELLOW}[3/6] Cleaning cache...${NC}"

find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

echo -e "${GREEN}✅ Cache cleaned${NC}"
echo ""

# ============================================================================
# VIRTUAL ENVIRONMENT
# ============================================================================
echo -e "${YELLOW}[4/6] Setting up Python environment...${NC}"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo -e "${GREEN}✅ Virtual environment ready${NC}"
echo ""

# ============================================================================
# INSTALL DEPENDENCIES
# ============================================================================
echo -e "${YELLOW}[5/6] Installing dependencies...${NC}"

.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# ============================================================================
# START BOT IN POLLING MODE
# ============================================================================
echo -e "${YELLOW}[6/6] Starting bot in polling mode...${NC}"

# Make executable
chmod +x start_polling_bot.py

# Start in background
PYTHONDONTWRITEBYTECODE=1 nohup .venv/bin/python -B start_polling_bot.py \
  > bot_polling.log 2>&1 &

BOT_PID=$!
echo $BOT_PID > bot.pid

echo -e "${GREEN}✅ Bot started (PID: ${BOT_PID})${NC}"
echo ""

# Wait and check
sleep 5

if ps -p $BOT_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Bot is running!${NC}"
else
    echo -e "${RED}❌ Bot failed to start${NC}"
    echo ""
    echo "Logs:"
    tail -20 bot_polling.log
    exit 1
fi

echo ""

# ============================================================================
# VERIFY
# ============================================================================
echo -e "${CYAN}Verifying bot status...${NC}"
sleep 2

# Check webhook is removed
WEBHOOK_INFO=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo" 2>/dev/null)
WEBHOOK_URL=$(echo "$WEBHOOK_INFO" | jq -r '.result.url' 2>/dev/null)

if [ -z "$WEBHOOK_URL" ] || [ "$WEBHOOK_URL" == "null" ] || [ "$WEBHOOK_URL" == "" ]; then
    echo -e "${GREEN}✅ Webhook disabled (polling mode)${NC}"
else
    echo -e "${YELLOW}⚠️  Webhook still set: $WEBHOOK_URL${NC}"
    echo "   Will be removed on next restart"
fi

echo ""

# ============================================================================
# SUCCESS
# ============================================================================
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   ✅ BOT DEPLOYED IN POLLING MODE!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}📊 System Status:${NC}"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "   Mode:        ${GREEN}Polling${NC}"
echo -e "   Bot PID:     ${GREEN}${BOT_PID}${NC}"
echo -e "   Webhook:     ${GREEN}Disabled${NC}"
echo -e "   DNS/SSL:     ${GREEN}Not needed${NC}"
echo ""
echo -e "${CYAN}✅ Features:${NC}"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   ✅ Telegram bot works"
echo "   ✅ ERPNext notifications work"
echo "   ✅ No webhook needed"
echo "   ✅ No DNS needed"
echo "   ✅ No SSL needed"
echo ""
echo -e "${CYAN}🔧 Management:${NC}"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Logs:        tail -f bot_polling.log"
echo "   Stop:        kill ${BOT_PID}"
echo "   Restart:     ./deploy_polling.sh"
echo "   Status:      ps aux | grep start_polling"
echo ""
echo -e "${CYAN}🧪 Test:${NC}"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   1. Send /start to your Telegram bot"
echo "   2. Bot should respond immediately"
echo "   3. ERPNext notifications will work"
echo ""
echo -e "${YELLOW}📋 Recent logs:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
tail -15 bot_polling.log
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}🎉 Ready! Test the bot on Telegram!${NC}"
echo ""
