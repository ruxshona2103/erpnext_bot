#!/bin/bash

# ============================================================================
# DEPLOYMENT DIAGNOSTIC SCRIPT
# Check if bot is running and which version is deployed
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}   DEPLOYMENT DIAGNOSTIC TOOL${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ============================================================================
# 1. CHECK RUNNING PROCESSES
# ============================================================================
echo -e "${YELLOW}[1/5] Checking running bot processes...${NC}"
echo ""

PROCESSES=$(ps aux | grep -E "(start_polling_bot|python.*app.main|uvicorn.*erpnext)" | grep -v grep)

if [ -n "$PROCESSES" ]; then
    echo -e "${GREEN}✅ Bot processes found:${NC}"
    echo "$PROCESSES"
else
    echo -e "${RED}❌ No bot processes running${NC}"
fi

echo ""

# ============================================================================
# 2. CHECK PID FILE
# ============================================================================
echo -e "${YELLOW}[2/5] Checking PID file...${NC}"
echo ""

if [ -f "bot.pid" ]; then
    PID=$(cat bot.pid)
    echo "PID file exists: $PID"

    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Process $PID is running${NC}"
    else
        echo -e "${RED}❌ Process $PID is NOT running (stale PID file)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No bot.pid file found${NC}"
fi

echo ""

# ============================================================================
# 3. CHECK GIT STATUS
# ============================================================================
echo -e "${YELLOW}[3/5] Checking git repository status...${NC}"
echo ""

if [ -d ".git" ]; then
    echo "Current branch: $(git branch --show-current)"
    echo "Current commit: $(git rev-parse --short HEAD) - $(git log -1 --format='%s')"
    echo ""
    echo "Remote status:"
    git fetch origin main 2>/dev/null
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main)

    if [ "$LOCAL" = "$REMOTE" ]; then
        echo -e "${GREEN}✅ Local is up to date with remote${NC}"
    else
        echo -e "${RED}❌ Local is BEHIND remote${NC}"
        echo "You need to pull changes!"
        echo ""
        echo "Commits behind:"
        git log --oneline HEAD..origin/main
    fi
else
    echo -e "${YELLOW}⚠️  Not a git repository${NC}"
fi

echo ""

# ============================================================================
# 4. CHECK RECENT LOGS
# ============================================================================
echo -e "${YELLOW}[4/5] Checking recent logs...${NC}"
echo ""

if [ -f "bot_polling.log" ]; then
    echo "Last 15 lines of bot_polling.log:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -15 bot_polling.log
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Check for errors
    ERRORS=$(grep -i "error\|exception\|failed" bot_polling.log | tail -5)
    if [ -n "$ERRORS" ]; then
        echo -e "${RED}Recent errors found:${NC}"
        echo "$ERRORS"
    else
        echo -e "${GREEN}✅ No recent errors in logs${NC}"
    fi
else
    echo -e "${RED}❌ No bot_polling.log file found${NC}"
fi

echo ""

# ============================================================================
# 5. CHECK DEPLOYMENT FILES
# ============================================================================
echo -e "${YELLOW}[5/5] Checking deployment files...${NC}"
echo ""

echo "Key files:"
[ -f "start_polling_bot.py" ] && echo -e "  ${GREEN}✅${NC} start_polling_bot.py" || echo -e "  ${RED}❌${NC} start_polling_bot.py"
[ -f ".env" ] && echo -e "  ${GREEN}✅${NC} .env" || echo -e "  ${RED}❌${NC} .env"
[ -f "deploy_polling.sh" ] && echo -e "  ${GREEN}✅${NC} deploy_polling.sh" || echo -e "  ${RED}❌${NC} deploy_polling.sh"
[ -f "deploy_improved.sh" ] && echo -e "  ${GREEN}✅${NC} deploy_improved.sh" || echo -e "  ${RED}❌${NC} deploy_improved.sh"
[ -d ".venv" ] && echo -e "  ${GREEN}✅${NC} .venv/" || echo -e "  ${RED}❌${NC} .venv/"
[ -d "app" ] && echo -e "  ${GREEN}✅${NC} app/" || echo -e "  ${RED}❌${NC} app/"

echo ""
echo "Code files modification times:"
ls -lh app/handlers/start.py 2>/dev/null || echo "  start.py not found"
ls -lh app/loader.py 2>/dev/null || echo "  loader.py not found"

echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}   DIAGNOSTIC SUMMARY${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ -n "$PROCESSES" ] && [ "$LOCAL" = "$REMOTE" ]; then
    echo -e "${GREEN}✅ Bot is running and up to date${NC}"
elif [ -n "$PROCESSES" ] && [ "$LOCAL" != "$REMOTE" ]; then
    echo -e "${YELLOW}⚠️  Bot is running but CODE IS OUTDATED${NC}"
    echo "   Action needed: Run ./deploy_improved.sh to update"
elif [ -z "$PROCESSES" ]; then
    echo -e "${RED}❌ Bot is NOT running${NC}"
    echo "   Action needed: Run ./deploy_improved.sh to start"
fi

echo ""
