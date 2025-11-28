#!/bin/bash

# ============================================================================
# DNS CHECK SCRIPT - DNS Muammosini Topish
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
echo "   DNS DIAGNOSTICS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"
echo ""

# Load .env
if [ -f ".env" ]; then
    source .env 2>/dev/null || export $(cat .env | grep -v '^#' | xargs)
    DOMAIN=$(echo $WEBHOOK_URL | sed -e 's|^[^/]*//||' -e 's|/.*$||')
else
    echo -e "${RED}❌ .env file not found!${NC}"
    exit 1
fi

# Get server IP
SERVER_IP=$(curl -s ifconfig.me)

echo -e "${CYAN}Configuration:${NC}"
echo "   Domain:    $DOMAIN"
echo "   Server IP: $SERVER_IP"
echo ""

# ============================================================================
# 1. DNS LOOKUP
# ============================================================================
echo -e "${YELLOW}[1/5] DNS Lookup...${NC}"
echo ""

DNS_RESULT=$(nslookup $DOMAIN 2>&1)
echo "$DNS_RESULT"
echo ""

DNS_IP=$(echo "$DNS_RESULT" | grep "Address:" | tail -1 | awk '{print $2}')

if [ -z "$DNS_IP" ]; then
    echo -e "${RED}❌ DNS not configured!${NC}"
    echo ""
    echo -e "${YELLOW}Please configure DNS:${NC}"
    echo "   Domain: $DOMAIN"
    echo "   Type: A Record"
    echo "   Value: $SERVER_IP"
    echo ""
    exit 1
elif [ "$DNS_IP" == "$SERVER_IP" ]; then
    echo -e "${GREEN}✅ DNS configured correctly${NC}"
    echo "   $DOMAIN → $DNS_IP"
else
    echo -e "${RED}❌ DNS points to wrong IP!${NC}"
    echo "   Expected: $SERVER_IP"
    echo "   Found:    $DNS_IP"
    echo ""
    echo -e "${YELLOW}Please update DNS:${NC}"
    echo "   Domain: $DOMAIN"
    echo "   Type: A Record"
    echo "   Value: $SERVER_IP"
    exit 1
fi

echo ""

# ============================================================================
# 2. PING TEST
# ============================================================================
echo -e "${YELLOW}[2/5] Ping Test...${NC}"

if ping -c 3 $DOMAIN > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Domain is reachable${NC}"
else
    echo -e "${RED}❌ Domain is NOT reachable${NC}"
fi

echo ""

# ============================================================================
# 3. HTTP TEST (Port 80)
# ============================================================================
echo -e "${YELLOW}[3/5] HTTP Test (port 80)...${NC}"

HTTP_TEST=$(curl -s --max-time 5 -o /dev/null -w "%{http_code}" http://$DOMAIN/ 2>&1)

if [ "$HTTP_TEST" == "200" ] || [ "$HTTP_TEST" == "301" ] || [ "$HTTP_TEST" == "302" ]; then
    echo -e "${GREEN}✅ HTTP accessible (code: $HTTP_TEST)${NC}"
else
    echo -e "${RED}❌ HTTP NOT accessible (code: $HTTP_TEST)${NC}"
fi

echo ""

# ============================================================================
# 4. DNS PROPAGATION CHECK
# ============================================================================
echo -e "${YELLOW}[4/5] DNS Propagation Check...${NC}"
echo ""

echo "Checking from different DNS servers:"

# Google DNS
GOOGLE_DNS=$(dig @8.8.8.8 $DOMAIN +short | head -1)
echo "   Google DNS (8.8.8.8):     $GOOGLE_DNS"

# Cloudflare DNS
CF_DNS=$(dig @1.1.1.1 $DOMAIN +short | head -1)
echo "   Cloudflare DNS (1.1.1.1): $CF_DNS"

# Local DNS
LOCAL_DNS=$(dig $DOMAIN +short | head -1)
echo "   Local DNS:                $LOCAL_DNS"

echo ""

if [ "$GOOGLE_DNS" == "$SERVER_IP" ] && [ "$CF_DNS" == "$SERVER_IP" ]; then
    echo -e "${GREEN}✅ DNS fully propagated${NC}"
elif [ -z "$GOOGLE_DNS" ] || [ -z "$CF_DNS" ]; then
    echo -e "${YELLOW}⚠️  DNS still propagating (wait 5-10 minutes)${NC}"
else
    echo -e "${RED}❌ DNS not propagated or incorrect${NC}"
fi

echo ""

# ============================================================================
# 5. FIREWALL CHECK
# ============================================================================
echo -e "${YELLOW}[5/5] Firewall Check...${NC}"

if command -v ufw >/dev/null 2>&1; then
    UFW_STATUS=$(ufw status | grep "80/tcp")
    if echo "$UFW_STATUS" | grep -q "ALLOW"; then
        echo -e "${GREEN}✅ Port 80 allowed${NC}"
    else
        echo -e "${RED}❌ Port 80 NOT allowed${NC}"
        echo "   Run: ufw allow 80/tcp"
    fi
else
    echo -e "${YELLOW}⚠️  UFW not installed${NC}"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   SUMMARY${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$DNS_IP" == "$SERVER_IP" ] && [ "$GOOGLE_DNS" == "$SERVER_IP" ]; then
    echo -e "${GREEN}✅ DNS is configured correctly!${NC}"
    echo ""
    echo "You can now get SSL certificate:"
    echo "   ./deploy_root.sh"
else
    echo -e "${RED}❌ DNS issues found!${NC}"
    echo ""
    echo -e "${YELLOW}Action required:${NC}"

    if [ "$DNS_IP" != "$SERVER_IP" ]; then
        echo "1. Update DNS A record:"
        echo "   Domain: $DOMAIN"
        echo "   Type: A"
        echo "   Value: $SERVER_IP"
        echo ""
    fi

    if [ "$GOOGLE_DNS" != "$SERVER_IP" ]; then
        echo "2. Wait for DNS propagation (5-10 minutes)"
        echo ""
    fi

    echo "3. Re-run this script to verify:"
    echo "   ./check_dns.sh"
fi

echo ""
