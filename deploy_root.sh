#!/bin/bash

# ============================================================================
# PROFESSIONAL PRODUCTION DEPLOYMENT - ROOT MODE
# Faqat erpnext_bot papkasida ishlaydi
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
echo "   PROFESSIONAL BOT DEPLOYMENT (ROOT MODE)"
echo "   Nginx + SSL + Webhook"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"
echo ""

# Get script directory and stay there
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${CYAN}📁 Working directory: ${SCRIPT_DIR}${NC}"
echo ""

# ============================================================================
# CHECK .env
# ============================================================================
echo -e "${YELLOW}[1/8] Checking configuration...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo ""
    echo "Creating .env from example..."
    cp .env.example .env
    echo ""
    echo -e "${YELLOW}📝 Please edit .env file:${NC}"
    echo "   nano .env"
    echo ""
    echo "Set these values:"
    echo "   BOT_TOKEN=your_token"
    echo "   WEBHOOK_URL=https://bot.macone.net"
    echo "   ERP credentials"
    echo ""
    exit 1
fi

# Load .env
source .env 2>/dev/null || export $(cat .env | grep -v '^#' | xargs)

# Validate
if [ -z "$BOT_TOKEN" ] || [ "$BOT_TOKEN" == "your_bot_token_here" ]; then
    echo -e "${RED}❌ BOT_TOKEN not set in .env${NC}"
    exit 1
fi

if [ -z "$WEBHOOK_URL" ]; then
    echo -e "${RED}❌ WEBHOOK_URL not set in .env${NC}"
    exit 1
fi

DOMAIN=$(echo $WEBHOOK_URL | sed -e 's|^[^/]*//||' -e 's|/.*$||')
BOT_PORT=${PORT:-8001}

echo -e "${GREEN}✅ Configuration loaded${NC}"
echo "   Domain: ${DOMAIN}"
echo "   Port: ${BOT_PORT}"
echo "   Webhook: ${WEBHOOK_URL}/webhook"
echo ""

# ============================================================================
# INSTALL PACKAGES
# ============================================================================
echo -e "${YELLOW}[2/8] Installing system packages...${NC}"

export DEBIAN_FRONTEND=noninteractive

apt-get update -qq
apt-get install -y -qq nginx certbot python3-certbot-nginx python3-venv python3-pip lsof curl jq > /dev/null 2>&1

echo -e "${GREEN}✅ Packages installed${NC}"
echo ""

# ============================================================================
# FIREWALL
# ============================================================================
echo -e "${YELLOW}[3/8] Configuring firewall...${NC}"

if command -v ufw >/dev/null 2>&1; then
    ufw --force enable > /dev/null 2>&1 || true
    ufw allow 80/tcp > /dev/null 2>&1 || true
    ufw allow 443/tcp > /dev/null 2>&1 || true
    ufw allow 22/tcp > /dev/null 2>&1 || true
    echo -e "${GREEN}✅ Firewall configured${NC}"
else
    echo -e "${YELLOW}⚠️  UFW not available, skipping${NC}"
fi
echo ""

# ============================================================================
# SSL CERTIFICATE
# ============================================================================
echo -e "${YELLOW}[4/8] Setting up SSL certificate...${NC}"

if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo -e "${GREEN}✅ SSL certificate already exists${NC}"
else
    echo "Getting SSL for ${DOMAIN}..."
    echo ""

    # Get server IP
    SERVER_IP=$(curl -s ifconfig.me)
    echo -e "${CYAN}Server IP: ${SERVER_IP}${NC}"
    echo -e "${YELLOW}Make sure DNS points ${DOMAIN} → ${SERVER_IP}${NC}"
    echo ""

    certbot certonly \
        --nginx \
        -d "$DOMAIN" \
        --non-interactive \
        --agree-tos \
        --email "admin@${DOMAIN}" \
        --redirect 2>&1 | grep -v "Saving debug log" || true

    if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
        echo -e "${GREEN}✅ SSL certificate obtained${NC}"
    else
        echo -e "${RED}❌ Failed to get SSL certificate${NC}"
        echo "Please check DNS configuration"
        exit 1
    fi
fi
echo ""

# ============================================================================
# NGINX CONFIGURATION
# ============================================================================
echo -e "${YELLOW}[5/8] Configuring Nginx...${NC}"

NGINX_CONF="/etc/nginx/sites-available/${DOMAIN}"

cat > "$NGINX_CONF" <<EOF
# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

# HTTPS configuration
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN};

    # SSL
    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/${DOMAIN}/chain.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Logs
    access_log /var/log/nginx/${DOMAIN}.access.log;
    error_log /var/log/nginx/${DOMAIN}.error.log;

    client_max_body_size 20M;

    # Telegram webhook
    location /webhook {
        proxy_pass http://127.0.0.1:${BOT_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # ERPNext webhook
    location /webhook/payment-entry {
        proxy_pass http://127.0.0.1:${BOT_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Health check
    location / {
        proxy_pass http://127.0.0.1:${BOT_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

# Enable site
ln -sf "$NGINX_CONF" "/etc/nginx/sites-enabled/${DOMAIN}"
rm -f /etc/nginx/sites-enabled/default

# Test and reload
nginx -t 2>&1 | tail -2
systemctl reload nginx

echo -e "${GREEN}✅ Nginx configured and reloaded${NC}"
echo ""

# ============================================================================
# STOP OLD BOT
# ============================================================================
echo -e "${YELLOW}[6/8] Stopping old bot processes...${NC}"

pkill -9 -f "uvicorn.*erpnext_bot" 2>/dev/null || true
pkill -9 -f "python.*app.webhook" 2>/dev/null || true

if lsof -ti:${BOT_PORT} > /dev/null 2>&1; then
    kill -9 $(lsof -ti:${BOT_PORT}) 2>/dev/null || true
fi

sleep 2

echo -e "${GREEN}✅ Old processes stopped${NC}"
echo ""

# ============================================================================
# CLEAN CACHE
# ============================================================================
echo -e "${YELLOW}[7/8] Cleaning cache...${NC}"

find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

echo -e "${GREEN}✅ Cache cleaned${NC}"
echo ""

# ============================================================================
# DEPLOY BOT
# ============================================================================
echo -e "${YELLOW}[8/8] Deploying bot...${NC}"

# Virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Install dependencies
echo "Installing dependencies..."
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

echo -e "${GREEN}✅ Dependencies installed${NC}"

# Start bot
echo "Starting bot on port ${BOT_PORT}..."

PYTHONDONTWRITEBYTECODE=1 nohup .venv/bin/python -B -m uvicorn app.webhook.server:app \
  --host 0.0.0.0 \
  --port ${BOT_PORT} \
  --log-level info \
  > bot.log 2>&1 &

BOT_PID=$!
echo $BOT_PID > bot.pid

echo -e "${GREEN}✅ Bot started (PID: ${BOT_PID})${NC}"
echo ""

# Wait for bot
sleep 5

# Check if running
if ps -p $BOT_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Bot is running${NC}"
else
    echo -e "${RED}❌ Bot failed to start${NC}"
    echo ""
    echo "Last 20 lines of log:"
    tail -20 bot.log
    exit 1
fi

echo ""

# ============================================================================
# VERIFY
# ============================================================================
echo -e "${CYAN}Verifying deployment...${NC}"
echo ""

sleep 3

# Check webhook
WEBHOOK_INFO=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo")

if echo "$WEBHOOK_INFO" | grep -q "\"url\":\"${WEBHOOK_URL}/webhook\""; then
    echo -e "${GREEN}✅ Webhook set correctly${NC}"
else
    echo -e "${YELLOW}⚠️  Webhook status:${NC}"
    echo "$WEBHOOK_INFO" | jq '.result.url' 2>/dev/null || echo "$WEBHOOK_INFO"
fi

# Check HTTPS endpoint
if curl -s -k --max-time 5 "https://${DOMAIN}/" 2>/dev/null | grep -q "status"; then
    echo -e "${GREEN}✅ HTTPS endpoint working${NC}"
fi

# Check local endpoint
if curl -s --max-time 5 "http://localhost:${BOT_PORT}/" 2>/dev/null | grep -q "status"; then
    echo -e "${GREEN}✅ Local endpoint working${NC}"
fi

echo ""

# ============================================================================
# SUCCESS
# ============================================================================
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   ✅ DEPLOYMENT SUCCESSFUL!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}📊 System Status:${NC}"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "   Domain:      ${GREEN}${DOMAIN}${NC}"
echo -e "   SSL:         ${GREEN}✅ Active${NC}"
echo -e "   Nginx:       ${GREEN}✅ Running${NC}"
echo -e "   Bot PID:     ${GREEN}${BOT_PID}${NC}"
echo -e "   Port:        ${GREEN}${BOT_PORT}${NC}"
echo -e "   Webhook:     ${GREEN}${WEBHOOK_URL}/webhook${NC}"
echo ""
echo -e "${CYAN}🔧 Management:${NC}"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Logs:        tail -f bot.log"
echo "   Status:      ./check_status.sh"
echo "   Restart:     ./production_deploy.sh"
echo "   Stop:        kill ${BOT_PID}"
echo ""
echo -e "${CYAN}🧪 Test:${NC}"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Send /start to your Telegram bot"
echo ""
echo -e "${YELLOW}📋 Recent logs:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
tail -15 bot.log
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}🎉 Bot is ready! Test it on Telegram!${NC}"
echo ""
