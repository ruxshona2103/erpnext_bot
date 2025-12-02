#!/bin/bash

# ============================================================================
# BOT DEBUG SCRIPT - MUAMMONI TOPISH
# Bu script botning haqiqiy holatini chuqur tekshiradi
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}   BOT DEBUG - MUAMMONI TOPISH${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ============================================================================
# 1. KOD VERSIYASINI TEKSHIRISH
# ============================================================================
echo -e "${YELLOW}[1/8] Kod versiyasini tekshirish...${NC}"
echo ""

if [ -d ".git" ]; then
    CURRENT_COMMIT=$(git rev-parse --short HEAD)
    CURRENT_BRANCH=$(git branch --show-current)

    echo "Git branch: $CURRENT_BRANCH"
    echo "Current commit: $CURRENT_COMMIT"
    echo ""
    echo "Last 3 commits:"
    git log --oneline -3
    echo ""

    # Check if /help command exists in code
    echo "Checking if /help command exists in code:"
    if grep -r "help.*command\|Command.*help" app/handlers/start.py > /dev/null; then
        echo -e "${GREEN}✅ /help command code FOUND in app/handlers/start.py${NC}"

        # Show the actual help command code
        echo ""
        echo "Help command in code:"
        grep -A 5 "async def help_message" app/handlers/start.py | head -10
    else
        echo -e "${RED}❌ /help command code NOT FOUND${NC}"
    fi

    echo ""

    # Check if bot commands are set in loader.py
    echo "Checking if bot commands auto-set code exists:"
    if grep -r "set_my_commands\|BotCommand" app/loader.py > /dev/null; then
        echo -e "${GREEN}✅ Bot commands auto-set code FOUND in app/loader.py${NC}"
    else
        echo -e "${RED}❌ Bot commands auto-set code NOT FOUND${NC}"
    fi
else
    echo -e "${RED}❌ Not a git repository${NC}"
fi

echo ""

# ============================================================================
# 2. RUNNING PROCESS TEKSHIRISH
# ============================================================================
echo -e "${YELLOW}[2/8] Running processes...${NC}"
echo ""

PROCESSES=$(ps aux | grep -E "(start_polling|python.*erpnext)" | grep -v grep)

if [ -n "$PROCESSES" ]; then
    echo -e "${GREEN}✅ Found bot processes:${NC}"
    echo "$PROCESSES"

    # Get PID
    BOT_PID=$(echo "$PROCESSES" | awk '{print $2}' | head -1)
    echo ""
    echo "Main bot PID: $BOT_PID"

    # Check process start time
    PS_START=$(ps -p $BOT_PID -o lstart= 2>/dev/null)
    if [ -n "$PS_START" ]; then
        echo "Process started: $PS_START"
    fi
else
    echo -e "${RED}❌ No bot processes running${NC}"
    BOT_PID=""
fi

echo ""

# ============================================================================
# 3. FAYLLAR MODIFICATION TIME
# ============================================================================
echo -e "${YELLOW}[3/8] Fayllar modification time...${NC}"
echo ""

echo "Code files last modified:"
ls -lh --time-style=long-iso app/handlers/start.py 2>/dev/null | awk '{print $6, $7, $8}'
ls -lh --time-style=long-iso app/loader.py 2>/dev/null | awk '{print $6, $7, $8}'
ls -lh --time-style=long-iso start_polling_bot.py 2>/dev/null | awk '{print $6, $7, $8}'

echo ""

# ============================================================================
# 4. PYTHON CACHE TEKSHIRISH
# ============================================================================
echo -e "${YELLOW}[4/8] Python cache files...${NC}"
echo ""

CACHE_COUNT=$(find . -type f -name "*.pyc" 2>/dev/null | wc -l)
PYCACHE_COUNT=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)

if [ $CACHE_COUNT -gt 0 ] || [ $PYCACHE_COUNT -gt 0 ]; then
    echo -e "${RED}⚠️  WARNING: Python cache exists!${NC}"
    echo "   .pyc files: $CACHE_COUNT"
    echo "   __pycache__ dirs: $PYCACHE_COUNT"
    echo ""
    echo "   This might cause old code to run!"
    echo "   Run: find . -name '*.pyc' -delete && find . -name '__pycache__' -exec rm -rf {} +"
else
    echo -e "${GREEN}✅ No Python cache files${NC}"
fi

echo ""

# ============================================================================
# 5. LOG FAYLNI TEKSHIRISH
# ============================================================================
echo -e "${YELLOW}[5/8] Bot logs...${NC}"
echo ""

if [ -f "bot_polling.log" ]; then
    LOG_SIZE=$(du -h bot_polling.log | cut -f1)
    echo "Log file size: $LOG_SIZE"
    echo ""

    echo "Last 15 lines:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -15 bot_polling.log
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Check for command registration
    if grep -i "command.*success\|set_my_commands" bot_polling.log | tail -5 | head -3; then
        echo -e "${GREEN}✅ Commands registration found in logs${NC}"
    else
        echo -e "${RED}⚠️  No command registration in logs${NC}"
    fi

    echo ""

    # Check for errors
    ERROR_COUNT=$(grep -i "error\|exception\|failed" bot_polling.log | wc -l)
    if [ $ERROR_COUNT -gt 0 ]; then
        echo -e "${RED}Found $ERROR_COUNT errors in logs:${NC}"
        grep -i "error\|exception\|failed" bot_polling.log | tail -5
    else
        echo -e "${GREEN}✅ No errors in logs${NC}"
    fi
else
    echo -e "${RED}❌ bot_polling.log not found${NC}"
fi

echo ""

# ============================================================================
# 6. ENVIRONMENT TEKSHIRISH
# ============================================================================
echo -e "${YELLOW}[6/8] Environment check...${NC}"
echo ""

if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"

    # Check BOT_TOKEN (show first 20 chars only)
    if grep -q "BOT_TOKEN=" .env; then
        TOKEN=$(grep "BOT_TOKEN=" .env | cut -d'=' -f2 | head -c 20)
        echo "BOT_TOKEN: ${TOKEN}..."
    else
        echo -e "${RED}❌ BOT_TOKEN not found in .env${NC}"
    fi
else
    echo -e "${RED}❌ .env file not found${NC}"
fi

echo ""

# ============================================================================
# 7. ACTUAL CODE CONTENT
# ============================================================================
echo -e "${YELLOW}[7/8] Actual code in start.py...${NC}"
echo ""

if [ -f "app/handlers/start.py" ]; then
    # Check if help_message function exists
    if grep -q "async def help_message" app/handlers/start.py; then
        echo -e "${GREEN}✅ help_message function EXISTS${NC}"
        echo ""

        # Show function signature and first few lines
        echo "Function preview:"
        grep -A 15 "async def help_message" app/handlers/start.py | head -20
    else
        echo -e "${RED}❌ help_message function NOT FOUND${NC}"
    fi

    echo ""

    # Check if register_start_handlers registers help
    if grep -q 'Command.*"help"' app/handlers/start.py; then
        echo -e "${GREEN}✅ /help command IS REGISTERED${NC}"
    else
        echo -e "${RED}❌ /help command NOT REGISTERED${NC}"
    fi
else
    echo -e "${RED}❌ app/handlers/start.py not found${NC}"
fi

echo ""

# ============================================================================
# 8. PROCESS ENVIRONMENT
# ============================================================================
echo -e "${YELLOW}[8/8] Process environment...${NC}"
echo ""

if [ -n "$BOT_PID" ]; then
    echo "Process CWD (working directory):"
    ls -l /proc/$BOT_PID/cwd 2>/dev/null || echo "Cannot read process cwd"

    echo ""
    echo "Process command line:"
    cat /proc/$BOT_PID/cmdline 2>/dev/null | tr '\0' ' ' || echo "Cannot read process cmdline"

    echo ""
else
    echo -e "${RED}No bot process to check${NC}"
fi

echo ""

# ============================================================================
# XULOSALAR
# ============================================================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}   DIAGNOSTIKA XULOSALAR${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check all conditions
ISSUES=0

# 1. Check if code has help command
if ! grep -q "async def help_message" app/handlers/start.py 2>/dev/null; then
    echo -e "${RED}❌ MUAMMO: /help command kodi faylda yo'q${NC}"
    ISSUES=$((ISSUES + 1))
fi

# 2. Check if bot is running
if [ -z "$BOT_PID" ]; then
    echo -e "${RED}❌ MUAMMO: Bot process ishlamayapti${NC}"
    ISSUES=$((ISSUES + 1))
fi

# 3. Check if cache exists
if [ $CACHE_COUNT -gt 0 ] || [ $PYCACHE_COUNT -gt 0 ]; then
    echo -e "${YELLOW}⚠️  MUAMMO: Python cache mavjud (eski kod ishlaganida)${NC}"
    ISSUES=$((ISSUES + 1))
fi

# 4. Check process start time vs code modification
if [ -n "$BOT_PID" ] && [ -f "app/handlers/start.py" ]; then
    PROCESS_TIME=$(stat -c %Y /proc/$BOT_PID 2>/dev/null || echo 0)
    FILE_TIME=$(stat -c %Y app/handlers/start.py 2>/dev/null || echo 0)

    if [ $FILE_TIME -gt $PROCESS_TIME ]; then
        echo -e "${RED}❌ MUAMMO: Kod yangilangan, lekin bot qayta ishga tushmagan${NC}"
        echo "   Fayl yangilangan: $(date -d @$FILE_TIME)"
        echo "   Process boshlangan: $(date -d @$PROCESS_TIME)"
        ISSUES=$((ISSUES + 1))
    fi
fi

echo ""

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ Hech qanday muammo topilmadi${NC}"
    echo ""
    echo "Agar hali ham commandlar ko'rinmasa:"
    echo "1. Telegram botini /start bilan restart qiling"
    echo "2. BotFather orqali commandlarni qo'lda sozlang"
    echo "3. Bot tokenini tekshiring"
else
    echo -e "${RED}Topilgan muammolar: $ISSUES${NC}"
    echo ""
    echo "YECHIM:"
    echo "1. Cache'ni tozalang: find . -name '*.pyc' -delete"
    echo "2. Botni qayta ishga tushiring: ./deploy_improved.sh"
    echo "3. Loglarni kuzating: tail -f bot_polling.log"
fi

echo ""
