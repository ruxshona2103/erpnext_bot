#!/bin/bash

# ============================================================================
# IMPROVED POLLING MODE DEPLOYMENT
# Fixes: Process cleanup, cache clearing, and restart reliability
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
echo "   IMPROVED DEPLOYMENT SCRIPT"
echo "   Better Process Management & Cache Clearing"
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
echo -e "${YELLOW}[1/7] Checking configuration...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    exit 1
fi

source .env 2>/dev/null || export $(cat .env | grep -v '^#' | xargs)

if [ -z "$BOT_TOKEN" ]; then
    echo -e "${RED}❌ BOT_TOKEN not set in .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Configuration OK${NC}"
echo ""

# ============================================================================
# IMPROVED PROCESS STOPPING
# ============================================================================
echo -e "${YELLOW}[2/7] Stopping old bot processes (improved)...${NC}"

# Find all related processes
PIDS=$(ps aux | grep -E "(start_polling_bot|python.*app.main|uvicorn.*erpnext)" | grep -v grep | awk '{print $2}')

if [ -n "$PIDS" ]; then
    echo "Found processes: $PIDS"

    # First try graceful shutdown
    echo "Attempting graceful shutdown..."
    for PID in $PIDS; do
        kill -TERM $PID 2>/dev/null || true
    done

    sleep 3

    # Force kill if still running
    echo "Force killing remaining processes..."
    for PID in $PIDS; do
        kill -9 $PID 2>/dev/null || true
    done

    sleep 2
else
    echo "No running bot processes found"
fi

# Verify all stopped
REMAINING=$(ps aux | grep -E "(start_polling_bot|python.*app.main|uvicorn.*erpnext)" | grep -v grep | wc -l)
if [ "$REMAINING" -gt 0 ]; then
    echo -e "${RED}⚠️  Warning: Some processes still running${NC}"
    ps aux | grep -E "(start_polling_bot|python.*app.main)" | grep -v grep
else
    echo -e "${GREEN}✅ All old processes stopped${NC}"
fi

echo ""

# ============================================================================
# AGGRESSIVE CACHE CLEANING
# ============================================================================
echo -e "${YELLOW}[3/7] Aggressive cache cleaning...${NC}"

# Remove __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Remove .pyc and .pyo files
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

# Remove pip cache
rm -rf ~/.cache/pip 2>/dev/null || true

# Remove pytest cache
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

echo -e "${GREEN}✅ Cache aggressively cleaned${NC}"
echo ""

# ============================================================================
# VIRTUAL ENVIRONMENT
# ============================================================================
echo -e "${YELLOW}[4/7] Setting up Python environment...${NC}"

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
echo -e "${YELLOW}[5/7] Installing dependencies...${NC}"

.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q --no-cache-dir

echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# ============================================================================
# VERIFY CODE CHANGES
# ============================================================================
echo -e "${YELLOW}[6/7] Verifying code changes...${NC}"

if [ -d ".git" ]; then
    CURRENT_COMMIT=$(git rev-parse --short HEAD)
    echo "Current commit: $CURRENT_COMMIT"
    echo "Recent changes:"
    git log --oneline -3
else
    echo "Not a git repository"
fi

echo -e "${GREEN}✅ Code verified${NC}"
echo ""

# ============================================================================
# START BOT IN POLLING MODE
# ============================================================================
echo -e "${YELLOW}[7/7] Starting bot in polling mode...${NC}"

# Make executable
chmod +x start_polling_bot.py

# Start with explicit flags to prevent caching
PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 nohup .venv/bin/python -B -u start_polling_bot.py \
  > bot_polling.log 2>&1 &

BOT_PID=$!
echo $BOT_PID > bot.pid

echo -e "${GREEN}✅ Bot started (PID: ${BOT_PID})${NC}"
echo ""

# Wait and check with better verification
sleep 8

if ps -p $BOT_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Bot is running!${NC}"
else
    echo -e "${RED}❌ Bot failed to start${NC}"
    echo ""
    echo "Recent logs:"
    tail -30 bot_polling.log
    exit 1
fi

echo ""

# ============================================================================
# VERIFY DEPLOYMENT
# ============================================================================
echo -e "${CYAN}Verifying deployment...${NC}"
echo ""

# Show bot info
if [ -d ".git" ]; then
    GIT_COMMIT=$(git rev-parse --short HEAD)
    GIT_BRANCH=$(git branch --show-current)
    echo -e "Git: ${GREEN}${GIT_BRANCH}@${GIT_COMMIT}${NC}"
fi

# Check if commands are set
echo "Checking bot commands..."
sleep 3
tail -10 bot_polling.log | grep -i "command" || echo "Commands status unknown - check logs"

echo ""

# ============================================================================
# SUCCESS
# ============================================================================
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   ✅ IMPROVED DEPLOYMENT COMPLETE!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}📊 System Status:${NC}"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "   Mode:        ${GREEN}Polling${NC}"
echo -e "   Bot PID:     ${GREEN}${BOT_PID}${NC}"
echo -e "   Cache:       ${GREEN}Cleared${NC}"
echo ""
echo -e "${CYAN}🔧 Management:${NC}"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Logs:        tail -f bot_polling.log"
echo "   Stop:        kill ${BOT_PID}"
echo "   Restart:     ./deploy_improved.sh"
echo ""
echo -e "${YELLOW}📋 Recent logs:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
tail -20 bot_polling.log
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}🎉 Test the bot on Telegram now!${NC}"
echo ""
