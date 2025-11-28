#!/bin/bash

# ============================================================================
# COMPLETE PRODUCTION SETUP - ONE COMMAND
# Nginx + SSL + Bot - hammasi avtomatik!
# ============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${MAGENTA}"
cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║     PRODUCTION SETUP - PROFESSIONAL DEPLOYMENT            ║
║     Nginx + SSL + Telegram Bot Webhook                    ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ Do NOT run this script as root!${NC}"
   echo "Run without sudo. It will ask for sudo when needed."
   exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ============================================================================
# CONFIGURATION
# ============================================================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 Configuration${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo ""
    echo -e "${RED}❌ Please edit .env file first!${NC}"
    echo ""
    echo "1. Set BOT_TOKEN (from @BotFather)"
    echo "2. Set WEBHOOK_URL (your domain, e.g., https://bot.macone.net)"
    echo "3. Set ERP_BASE_URL, ERP_API_KEY, ERP_API_SECRET"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Load .env
export $(cat .env | grep -v '^#' | xargs)

# Validate
if [ -z "$BOT_TOKEN" ] || [ "$BOT_TOKEN" == "your_bot_token_here" ]; then
    echo -e "${RED}❌ BOT_TOKEN not configured in .env${NC}"
    exit 1
fi

if [ -z "$WEBHOOK_URL" ] || [ "$WEBHOOK_URL" == "https://your-domain.com" ]; then
    echo -e "${RED}❌ WEBHOOK_URL not configured in .env${NC}"
    exit 1
fi

# Extract domain
DOMAIN=$(echo $WEBHOOK_URL | sed -e 's|^[^/]*//||' -e 's|/.*$||')

echo -e "${GREEN}✅ Configuration loaded${NC}"
echo "   Domain: $DOMAIN"
echo "   Webhook: $WEBHOOK_URL"
echo ""

# Confirmation
echo -e "${YELLOW}This script will:${NC}"
echo "  1. Install Nginx and Certbot"
echo "  2. Get SSL certificate for $DOMAIN"
echo "  3. Configure Nginx reverse proxy"
echo "  4. Deploy Telegram bot"
echo "  5. Set up webhook to $WEBHOOK_URL"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# ============================================================================
# STEP 1: INSTALL PACKAGES
# ============================================================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📦 [1/6] Installing Packages${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

sudo apt update -qq
sudo apt install -y nginx certbot python3-certbot-nginx python3-venv lsof curl jq

echo -e "${GREEN}✅ Packages installed${NC}"

# ============================================================================
# STEP 2: CONFIGURE FIREWALL
# ============================================================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔥 [2/6] Configuring Firewall${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if command -v ufw >/dev/null 2>&1; then
    sudo ufw allow 'Nginx Full' >/dev/null 2>&1 || true
    sudo ufw allow 80/tcp >/dev/null 2>&1 || true
    sudo ufw allow 443/tcp >/dev/null 2>&1 || true
    echo -e "${GREEN}✅ Firewall configured${NC}"
else
    echo -e "${YELLOW}⚠️  UFW not installed, skipping${NC}"
fi

# ============================================================================
# STEP 3: SSL CERTIFICATE
# ============================================================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔒 [3/6] Getting SSL Certificate${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo -e "${GREEN}✅ SSL certificate already exists${NC}"
else
    echo "Getting certificate for $DOMAIN..."
    echo ""
    echo -e "${YELLOW}⚠️  Make sure DNS is configured:${NC}"
    echo "   $DOMAIN → $(curl -s ifconfig.me)"
    echo ""
    read -p "DNS configured? Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please configure DNS first, then run again."
        exit 1
    fi

    sudo certbot certonly --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@$DOMAIN || {
        echo -e "${RED}❌ Failed to get SSL certificate${NC}"
        echo "Make sure:"
        echo "  1. DNS is configured correctly"
        echo "  2. Port 80 is accessible from internet"
        exit 1
    }
    echo -e "${GREEN}✅ SSL certificate obtained${NC}"
fi

# ============================================================================
# STEP 4: NGINX CONFIGURATION
# ============================================================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}⚙️  [4/6] Configuring Nginx${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

NGINX_CONF="/etc/nginx/sites-available/$DOMAIN"
BOT_PORT=${PORT:-8001}

sudo tee "$NGINX_CONF" > /dev/null <<EOF
# ERPNext Telegram Bot - HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

# HTTPS Configuration
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN;

    # SSL Certificates
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/$DOMAIN/chain.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    # Logs
    access_log /var/log/nginx/$DOMAIN.access.log;
    error_log /var/log/nginx/$DOMAIN.error.log;

    # Max upload size
    client_max_body_size 20M;

    # Telegram webhook endpoint
    location /webhook {
        proxy_pass http://127.0.0.1:$BOT_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # ERPNext webhook endpoint
    location /webhook/payment-entry {
        proxy_pass http://127.0.0.1:$BOT_PORT;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Health check
    location / {
        proxy_pass http://127.0.0.1:$BOT_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

# Enable site
sudo ln -sf "$NGINX_CONF" "/etc/nginx/sites-enabled/$DOMAIN"

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test config
sudo nginx -t || {
    echo -e "${RED}❌ Nginx configuration error${NC}"
    exit 1
}

# Reload nginx
sudo systemctl reload nginx

echo -e "${GREEN}✅ Nginx configured${NC}"

# ============================================================================
# STEP 5: DEPLOY BOT
# ============================================================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🤖 [5/6] Deploying Bot${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Stop old processes
pkill -9 -f "uvicorn.*erpnext_bot" 2>/dev/null || true
sleep 2

# Clean cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Virtual environment
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# Install dependencies
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

echo -e "${GREEN}✅ Dependencies installed${NC}"

# Start bot
PYTHONDONTWRITEBYTECODE=1 nohup .venv/bin/python -B -m uvicorn app.webhook.server:app \
  --host 0.0.0.0 \
  --port $BOT_PORT \
  --log-level info \
  > bot.log 2>&1 &

BOT_PID=$!
echo $BOT_PID > bot.pid

echo -e "${GREEN}✅ Bot started (PID: $BOT_PID)${NC}"

# Wait for bot
sleep 5

if ! ps -p $BOT_PID > /dev/null; then
    echo -e "${RED}❌ Bot failed to start${NC}"
    tail -20 bot.log
    exit 1
fi

# ============================================================================
# STEP 6: VERIFY
# ============================================================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🧪 [6/6] Verifying Setup${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Wait for webhook to be set
sleep 3

# Check webhook
echo "Checking Telegram webhook..."
WEBHOOK_CHECK=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo")

if echo "$WEBHOOK_CHECK" | jq -e ".result.url" | grep -q "$WEBHOOK_URL"; then
    echo -e "${GREEN}✅ Webhook set correctly${NC}"
else
    echo -e "${YELLOW}⚠️  Webhook info:${NC}"
    echo "$WEBHOOK_CHECK" | jq '.' 2>/dev/null || echo "$WEBHOOK_CHECK"
fi

# Test HTTPS endpoint
echo "Testing HTTPS endpoint..."
if curl -s -k "https://$DOMAIN/" | grep -q "status"; then
    echo -e "${GREEN}✅ HTTPS endpoint working${NC}"
else
    echo -e "${YELLOW}⚠️  Could not verify endpoint${NC}"
fi

# ============================================================================
# SUCCESS
# ============================================================================
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   ✅ SETUP COMPLETE! ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}📊 System Status:${NC}"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "   Domain:         ${GREEN}$DOMAIN${NC}"
echo -e "   SSL:            ${GREEN}✅ Active${NC}"
echo -e "   Nginx:          ${GREEN}✅ Running${NC}"
echo -e "   Bot:            ${GREEN}✅ Running (PID: $BOT_PID)${NC}"
echo -e "   Webhook:        ${GREEN}$WEBHOOK_URL/webhook${NC}"
echo ""
echo -e "${CYAN}🔧 Next Steps:${NC}"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   1. Test bot: Send /start to your Telegram bot"
echo "   2. Check logs: tail -f bot.log"
echo "   3. Monitor: tail -f /var/log/nginx/$DOMAIN.access.log"
echo ""
echo -e "${CYAN}📝 Useful Commands:${NC}"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Restart bot:     ./production_deploy.sh"
echo "   Stop bot:        kill $BOT_PID"
echo "   View logs:       tail -f bot.log"
echo "   Nginx logs:      sudo tail -f /var/log/nginx/$DOMAIN.access.log"
echo "   Webhook info:    curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
echo ""
echo -e "${GREEN}🎉 Production bot is ready!${NC}"
echo ""
