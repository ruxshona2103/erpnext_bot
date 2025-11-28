#!/bin/bash

# ============================================================================
# BOT DEBUG SCRIPT - Muammoni Topish
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear

echo -e "${BLUE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   BOT DEBUG - MUAMMONI TOPISH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"
echo ""

# Load .env
if [ -f ".env" ]; then
    source .env 2>/dev/null || export $(cat .env | grep -v '^#' | xargs)
    DOMAIN=$(echo $WEBHOOK_URL | sed -e 's|^[^/]*//||' -e 's|/.*$||')
    BOT_PORT=${PORT:-8001}
else
    echo -e "${RED}❌ .env file not found!${NC}"
    exit 1
fi

# ============================================================================
# 1. BOT PROCESS
# ============================================================================
echo -e "${CYAN}[1/10] Checking bot process...${NC}"

if [ -f "bot.pid" ]; then
    BOT_PID=$(cat bot.pid)
    if ps -p $BOT_PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Bot process running (PID: $BOT_PID)${NC}"
    else
        echo -e "${RED}❌ Bot process NOT running (stale PID)${NC}"
        echo "   Last PID: $BOT_PID"
    fi
else
    echo -e "${RED}❌ No PID file found${NC}"
fi

# Check by process name
BOT_PROC=$(pgrep -f "uvicorn.*erpnext_bot" | head -1)
if [ -n "$BOT_PROC" ]; then
    echo -e "${GREEN}✅ Found bot process: $BOT_PROC${NC}"
else
    echo -e "${RED}❌ No bot process found${NC}"
fi

echo ""

# ============================================================================
# 2. BOT LOGS (JUDA MUHIM!)
# ============================================================================
echo -e "${CYAN}[2/10] Checking bot logs...${NC}"
echo ""

if [ -f "bot.log" ]; then
    echo -e "${YELLOW}Last 30 lines of bot.log:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -30 bot.log
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Check for errors
    ERROR_COUNT=$(grep -i "error\|exception\|failed" bot.log | wc -l)
    if [ $ERROR_COUNT -gt 0 ]; then
        echo -e "${RED}⚠️  Found $ERROR_COUNT errors!${NC}"
        echo ""
        echo -e "${YELLOW}Recent errors:${NC}"
        grep -i "error\|exception\|failed" bot.log | tail -10
        echo ""
    else
        echo -e "${GREEN}✅ No errors in logs${NC}"
    fi
else
    echo -e "${RED}❌ bot.log file not found${NC}"
fi

echo ""

# ============================================================================
# 3. PORT CHECK
# ============================================================================
echo -e "${CYAN}[3/10] Checking port ${BOT_PORT}...${NC}"

if lsof -i :$BOT_PORT > /dev/null 2>&1; then
    PROC_INFO=$(lsof -i :$BOT_PORT | tail -1)
    echo -e "${GREEN}✅ Port $BOT_PORT is in use${NC}"
    echo "   $PROC_INFO"
else
    echo -e "${RED}❌ Port $BOT_PORT is NOT in use${NC}"
    echo "   Bot is not listening!"
fi

echo ""

# ============================================================================
# 4. LOCAL ENDPOINT TEST
# ============================================================================
echo -e "${CYAN}[4/10] Testing local endpoint...${NC}"

LOCAL_RESPONSE=$(curl -s --max-time 3 http://localhost:$BOT_PORT/ 2>&1)

if echo "$LOCAL_RESPONSE" | grep -q "status"; then
    echo -e "${GREEN}✅ Local endpoint working${NC}"
    echo "   Response: $LOCAL_RESPONSE"
else
    echo -e "${RED}❌ Local endpoint NOT working${NC}"
    echo "   Response: $LOCAL_RESPONSE"
fi

echo ""

# ============================================================================
# 5. NGINX STATUS
# ============================================================================
echo -e "${CYAN}[5/10] Checking Nginx...${NC}"

if systemctl is-active --quiet nginx 2>/dev/null; then
    echo -e "${GREEN}✅ Nginx is running${NC}"

    if [ -f "/etc/nginx/sites-enabled/$DOMAIN" ]; then
        echo -e "${GREEN}✅ Site config exists${NC}"
    else
        echo -e "${RED}❌ Site config NOT found${NC}"
    fi

    # Test config
    if nginx -t 2>&1 | grep -q "successful"; then
        echo -e "${GREEN}✅ Nginx config valid${NC}"
    else
        echo -e "${RED}❌ Nginx config invalid${NC}"
        nginx -t 2>&1
    fi
else
    echo -e "${RED}❌ Nginx is NOT running${NC}"
fi

echo ""

# ============================================================================
# 6. SSL CHECK
# ============================================================================
echo -e "${CYAN}[6/10] Checking SSL...${NC}"

if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo -e "${GREEN}✅ SSL certificate exists${NC}"

    CERT_FILE="/etc/letsencrypt/live/$DOMAIN/cert.pem"
    if [ -f "$CERT_FILE" ]; then
        EXPIRY=$(openssl x509 -enddate -noout -in "$CERT_FILE" 2>/dev/null | cut -d= -f2)
        echo "   Expires: $EXPIRY"
    fi
else
    echo -e "${RED}❌ SSL certificate NOT found${NC}"
fi

echo ""

# ============================================================================
# 7. HTTPS ENDPOINT TEST
# ============================================================================
echo -e "${CYAN}[7/10] Testing HTTPS endpoint...${NC}"

HTTPS_RESPONSE=$(curl -s -k --max-time 5 https://$DOMAIN/ 2>&1)

if echo "$HTTPS_RESPONSE" | grep -q "status"; then
    echo -e "${GREEN}✅ HTTPS endpoint working${NC}"
    echo "   Response: $HTTPS_RESPONSE"
else
    echo -e "${RED}❌ HTTPS endpoint NOT working${NC}"
    echo "   Response: $HTTPS_RESPONSE"
fi

echo ""

# ============================================================================
# 8. WEBHOOK STATUS (ENG MUHIM!)
# ============================================================================
echo -e "${CYAN}[8/10] Checking Telegram webhook...${NC}"
echo ""

if [ -z "$BOT_TOKEN" ]; then
    echo -e "${RED}❌ BOT_TOKEN not found in .env${NC}"
else
    WEBHOOK_INFO=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo")

    echo -e "${YELLOW}Webhook Info:${NC}"
    echo "$WEBHOOK_INFO" | jq '.' 2>/dev/null || echo "$WEBHOOK_INFO"
    echo ""

    # Check URL
    CURRENT_URL=$(echo "$WEBHOOK_INFO" | jq -r '.result.url' 2>/dev/null)
    EXPECTED_URL="${WEBHOOK_URL}/webhook"

    if [ "$CURRENT_URL" == "$EXPECTED_URL" ]; then
        echo -e "${GREEN}✅ Webhook URL correct${NC}"
        echo "   URL: $CURRENT_URL"
    else
        echo -e "${RED}❌ Webhook URL mismatch!${NC}"
        echo "   Expected: $EXPECTED_URL"
        echo "   Current:  $CURRENT_URL"
    fi

    # Check pending updates
    PENDING=$(echo "$WEBHOOK_INFO" | jq -r '.result.pending_update_count' 2>/dev/null)
    if [ "$PENDING" != "null" ] && [ "$PENDING" != "0" ]; then
        echo -e "${YELLOW}⚠️  Pending updates: $PENDING${NC}"
    fi

    # Check last error
    LAST_ERROR=$(echo "$WEBHOOK_INFO" | jq -r '.result.last_error_message' 2>/dev/null)
    if [ "$LAST_ERROR" != "null" ] && [ -n "$LAST_ERROR" ]; then
        echo -e "${RED}❌ Last error: $LAST_ERROR${NC}"
    fi
fi

echo ""

# ============================================================================
# 9. NGINX LOGS
# ============================================================================
echo -e "${CYAN}[9/10] Checking Nginx logs...${NC}"

if [ -f "/var/log/nginx/${DOMAIN}.access.log" ]; then
    echo -e "${YELLOW}Last 10 access logs:${NC}"
    tail -10 /var/log/nginx/${DOMAIN}.access.log
    echo ""
fi

if [ -f "/var/log/nginx/${DOMAIN}.error.log" ]; then
    ERROR_LOG_COUNT=$(wc -l < /var/log/nginx/${DOMAIN}.error.log)
    if [ $ERROR_LOG_COUNT -gt 0 ]; then
        echo -e "${RED}⚠️  Found errors in Nginx log:${NC}"
        tail -10 /var/log/nginx/${DOMAIN}.error.log
        echo ""
    fi
fi

echo ""

# ============================================================================
# 10. DNS CHECK
# ============================================================================
echo -e "${CYAN}[10/10] Checking DNS...${NC}"

DNS_IP=$(nslookup $DOMAIN 2>/dev/null | grep "Address:" | tail -1 | awk '{print $2}')
SERVER_IP=$(curl -s ifconfig.me)

echo "   Domain: $DOMAIN"
echo "   DNS IP: $DNS_IP"
echo "   Server IP: $SERVER_IP"

if [ "$DNS_IP" == "$SERVER_IP" ]; then
    echo -e "${GREEN}✅ DNS configured correctly${NC}"
else
    echo -e "${RED}❌ DNS mismatch!${NC}"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   DIAGNOSTIC SUMMARY${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}Most likely issues:${NC}"
echo ""

# Check bot running
if ! pgrep -f "uvicorn.*erpnext_bot" > /dev/null; then
    echo -e "${RED}1. Bot is NOT running!${NC}"
    echo "   Fix: ./deploy_root.sh"
    echo ""
fi

# Check webhook
if [ "$CURRENT_URL" != "$EXPECTED_URL" ]; then
    echo -e "${RED}2. Webhook URL incorrect!${NC}"
    echo "   Expected: $EXPECTED_URL"
    echo "   Current:  $CURRENT_URL"
    echo "   Fix: Restart bot to reset webhook"
    echo ""
fi

# Check HTTPS
if ! echo "$HTTPS_RESPONSE" | grep -q "status"; then
    echo -e "${RED}3. HTTPS endpoint not accessible!${NC}"
    echo "   Fix: Check Nginx and SSL"
    echo ""
fi

echo -e "${CYAN}Next steps:${NC}"
echo "   1. Check bot logs: tail -f bot.log"
echo "   2. Check if bot is running: ps aux | grep uvicorn"
echo "   3. Restart bot: ./deploy_root.sh"
echo ""
