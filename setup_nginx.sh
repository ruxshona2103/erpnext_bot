#!/bin/bash

# ============================================================================
# NGINX + SSL SETUP SCRIPT
# Serverda Nginx va SSL sertifikat sozlash uchun
# ============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "=========================================="
echo "  Nginx + SSL Setup"
echo "=========================================="
echo -e "${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ This script should NOT be run as root${NC}"
   echo "Run without sudo. Sudo will be used when needed."
   exit 1
fi

# Get domain from user
echo -e "${YELLOW}Enter your domain (e.g., bot.macone.net):${NC}"
read -r DOMAIN

if [ -z "$DOMAIN" ]; then
    echo -e "${RED}❌ Domain cannot be empty${NC}"
    exit 1
fi

echo -e "${GREEN}Domain: $DOMAIN${NC}"
echo ""

# ============================================================================
# 1. INSTALL PACKAGES
# ============================================================================
echo -e "${YELLOW}[1/5] Installing required packages...${NC}"
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

echo -e "${GREEN}✅ Packages installed${NC}"

# ============================================================================
# 2. CONFIGURE FIREWALL
# ============================================================================
echo -e "${YELLOW}[2/5] Configuring firewall...${NC}"

# Check if ufw is installed
if command -v ufw >/dev/null 2>&1; then
    sudo ufw allow 'Nginx Full'
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    echo -e "${GREEN}✅ Firewall configured${NC}"
else
    echo -e "${YELLOW}⚠️  UFW not installed, skipping firewall setup${NC}"
fi

# ============================================================================
# 3. GET SSL CERTIFICATE
# ============================================================================
echo -e "${YELLOW}[3/5] Getting SSL certificate...${NC}"
echo -e "${BLUE}This will use Let's Encrypt to get a free SSL certificate${NC}"
echo ""

# Check if certificate already exists
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo -e "${YELLOW}⚠️  Certificate already exists for $DOMAIN${NC}"
    echo "Skipping SSL setup..."
else
    sudo certbot certonly --nginx -d "$DOMAIN"
    echo -e "${GREEN}✅ SSL certificate obtained${NC}"
fi

# ============================================================================
# 4. CREATE NGINX CONFIGURATION
# ============================================================================
echo -e "${YELLOW}[4/5] Creating Nginx configuration...${NC}"

NGINX_CONF="/etc/nginx/sites-available/$DOMAIN"

sudo tee "$NGINX_CONF" > /dev/null <<EOF
# Telegram Bot Webhook - HTTP to HTTPS redirect
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

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Logs
    access_log /var/log/nginx/$DOMAIN.access.log;
    error_log /var/log/nginx/$DOMAIN.error.log;

    # Client max body size
    client_max_body_size 20M;

    # Telegram webhook
    location /webhook {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # ERPNext webhooks
    location /webhook/payment-entry {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Health check
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

echo -e "${GREEN}✅ Nginx configuration created${NC}"

# ============================================================================
# 5. ENABLE AND TEST NGINX
# ============================================================================
echo -e "${YELLOW}[5/5] Enabling site and reloading Nginx...${NC}"

# Create symlink
sudo ln -sf "$NGINX_CONF" "/etc/nginx/sites-enabled/$DOMAIN"

# Remove default site if exists
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    sudo rm -f /etc/nginx/sites-enabled/default
fi

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

echo -e "${GREEN}✅ Nginx configured and reloaded${NC}"

# ============================================================================
# DONE
# ============================================================================
echo ""
echo -e "${BLUE}=========================================="
echo "  SETUP COMPLETE!"
echo "==========================================${NC}"
echo ""
echo -e "${GREEN}✅ SSL Certificate: /etc/letsencrypt/live/$DOMAIN/${NC}"
echo -e "${GREEN}✅ Nginx Config: $NGINX_CONF${NC}"
echo -e "${GREEN}✅ Webhook URL: https://$DOMAIN/webhook${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Update .env file:"
echo "   WEBHOOK_URL=https://$DOMAIN"
echo "   WEBHOOK_PATH=/webhook"
echo ""
echo "2. Deploy bot:"
echo "   ./deploy.sh"
echo ""
echo "3. Test webhook:"
echo "   curl https://$DOMAIN/"
echo ""
echo "4. Check webhook info:"
echo "   curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
echo ""
echo -e "${GREEN}Done! 🎉${NC}"
