!/bin/bash

# ============================================================================
# BOT STATUS CHECKER - Professional Monitoring
# ============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}"
echo "════════════════════════════════════════════════"
echo "   SYSTEM STATUS CHECK"
echo "════════════════════════════════════════════════"
echo -e "${NC}"

# Load .env if exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs 2>/dev/null)
    DOMAIN=$(echo $WEBHOOK_URL | sed -e 's|^[^/]*//||' -e 's|/.*$||' 2>/dev/null)
fi

# ============================================================================
# 1. BOT PROCESS
# ============================================================================
echo -e "${CYAN}🤖 Bot Process:${NC}"
if [ -f "bot.pid" ]; then
    BOT_PID=$(cat bot.pid)
    if ps -p $BOT_PID > /dev/null 2>&1; then
        UPTIME=$(ps -p $BOT_PID -o etime= | xargs)
        echo -e "   ${GREEN}✅ Running${NC} (PID: $BOT_PID, Uptime: $UPTIME)"
    else
        echo -e "   ${RED}❌ Not running${NC} (stale PID file)"
    fi
else
    if pgrep -f "uvicorn.*erpnext_bot" > /dev/null; then
        PID=$(pgrep -f "uvicorn.*erpnext_bot")
        echo -e "   ${YELLOW}⚠️  Running${NC} (PID: $PID, but no PID file)"
    else
        echo -e "   ${RED}❌ Not running${NC}"
    fi
fi

# ============================================================================
# 2. PORT STATUS
# ============================================================================
echo ""
echo -e "${CYAN}🔌 Port Status:${NC}"
PORT=${PORT:-8001}
if lsof -i :$PORT > /dev/null 2>&1; then
    PROC=$(lsof -i :$PORT | tail -1 | awk '{print $1, $2}')
    echo -e "   ${GREEN}✅ Port $PORT${NC} - $PROC"
else
    echo -e "   ${RED}❌ Port $PORT${NC} - Not in use"
fi

# ============================================================================
# 3. NGINX STATUS
# ============================================================================
echo ""
echo -e "${CYAN}⚙️  Nginx:${NC}"
if systemctl is-active --quiet nginx 2>/dev/null; then
    echo -e "   ${GREEN}✅ Running${NC}"

    if [ -n "$DOMAIN" ] && [ -f "/etc/nginx/sites-enabled/$DOMAIN" ]; then
        echo -e "   ${GREEN}✅ Config active${NC} for $DOMAIN"
    elif [ -n "$DOMAIN" ]; then
        echo -e "   ${YELLOW}⚠️  Config not found${NC} for $DOMAIN"
    fi
else
    echo -e "   ${RED}❌ Not running${NC}"
fi

# ============================================================================
# 4. SSL CERTIFICATE
# ============================================================================
echo ""
echo -e "${CYAN}🔒 SSL Certificate:${NC}"
if [ -n "$DOMAIN" ] && [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    CERT_FILE="/etc/letsencrypt/live/$DOMAIN/cert.pem"
    if [ -f "$CERT_FILE" ]; then
        EXPIRY=$(sudo openssl x509 -enddate -noout -in "$CERT_FILE" 2>/dev/null | cut -d= -f2)
        DAYS_LEFT=$(( ( $(date -d "$EXPIRY" +%s) - $(date +%s) ) / 86400 ))

        if [ $DAYS_LEFT -gt 30 ]; then
            echo -e "   ${GREEN}✅ Valid${NC} (expires in $DAYS_LEFT days)"
        elif [ $DAYS_LEFT -gt 0 ]; then
            echo -e "   ${YELLOW}⚠️  Expiring soon${NC} ($DAYS_LEFT days left)"
        else
            echo -e "   ${RED}❌ Expired${NC}"
        fi
    fi
else
    echo -e "   ${YELLOW}⚠️  Not configured${NC}"
fi

# ============================================================================
# 5. WEBHOOK STATUS
# ============================================================================
echo ""
echo -e "${CYAN}🌐 Webhook Status:${NC}"
if [ -n "$BOT_TOKEN" ]; then
    WEBHOOK_INFO=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo" 2>/dev/null)

    if echo "$WEBHOOK_INFO" | grep -q '"ok":true'; then
        WEBHOOK_URL_SET=$(echo "$WEBHOOK_INFO" | grep -o '"url":"[^"]*"' | cut -d'"' -f4)
        PENDING=$(echo "$WEBHOOK_INFO" | grep -o '"pending_update_count":[0-9]*' | cut -d':' -f2)
        LAST_ERROR=$(echo "$WEBHOOK_INFO" | grep -o '"last_error_message":"[^"]*"' | cut -d'"' -f4)

        if [ -n "$WEBHOOK_URL_SET" ]; then
            echo -e "   ${GREEN}✅ Set${NC} to: $WEBHOOK_URL_SET"

            if [ "$PENDING" -gt 0 ]; then
                echo -e "   ${YELLOW}⚠️  Pending updates:${NC} $PENDING"
            fi

            if [ -n "$LAST_ERROR" ]; then
                echo -e "   ${RED}❌ Last error:${NC} $LAST_ERROR"
            fi
        else
            echo -e "   ${YELLOW}⚠️  Not set${NC}"
        fi
    else
        echo -e "   ${RED}❌ Cannot check${NC} (invalid token?)"
    fi
else
    echo -e "   ${YELLOW}⚠️  BOT_TOKEN not found${NC}"
fi

# ============================================================================
# 6. ENDPOINT TEST
# ============================================================================
echo ""
echo -e "${CYAN}🧪 Endpoint Test:${NC}"
if [ -n "$DOMAIN" ]; then
    if curl -s -k --max-time 5 "https://$DOMAIN/" | grep -q "status" 2>/dev/null; then
        echo -e "   ${GREEN}✅ Accessible${NC} at https://$DOMAIN/"
    else
        echo -e "   ${RED}❌ Not accessible${NC}"
    fi
fi

# Local endpoint
if curl -s --max-time 5 "http://localhost:${PORT}/" | grep -q "status" 2>/dev/null; then
    echo -e "   ${GREEN}✅ Local endpoint${NC} working (port $PORT)"
else
    echo -e "   ${RED}❌ Local endpoint${NC} not responding"
fi

# ============================================================================
# 7. RECENT LOGS
# ============================================================================
echo ""
echo -e "${CYAN}📋 Recent Logs (last 10 lines):${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "bot.log" ]; then
    tail -10 bot.log
else
    echo "No log file found"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ============================================================================
# 8. ERRORS CHECK
# ============================================================================
echo ""
if [ -f "bot.log" ]; then
    ERROR_COUNT=$(grep -i "error\|failed\|exception" bot.log | tail -5 | wc -l)
    if [ $ERROR_COUNT -gt 0 ]; then
        echo -e "${RED}⚠️  Found $ERROR_COUNT recent errors:${NC}"
        grep -i "error\|failed\|exception" bot.log | tail -5
    else
        echo -e "${GREEN}✅ No recent errors${NC}"
    fi
fi

# ============================================================================
# SUMMARY
# ============================================================================
echo ""
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${CYAN}💡 Quick Actions:${NC}"
echo "   View live logs:  tail -f bot.log"
echo "   Restart bot:     ./production_deploy.sh"
echo "   Stop bot:        kill \$(cat bot.pid)"
if [ -n "$DOMAIN" ]; then
    echo "   Nginx logs:      sudo tail -f /var/log/nginx/$DOMAIN.access.log"
fi
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo ""
