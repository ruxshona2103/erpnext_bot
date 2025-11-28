#!/bin/bash

# ============================================================================
# PRODUCTION DEPLOY - PROFESSIONAL WEBHOOK DEPLOYMENT
# To'liq avtomatik deploy - bir buyruq bilan hammasi!
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}"
echo "================================================"
echo "   PRODUCTION WEBHOOK DEPLOYMENT"
echo "   Professional Setup with Nginx + SSL"
echo "================================================"
echo -e "${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

log_info() {
    echo -e "${BLUE}ℹ ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠️ ${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

log_step() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}▶ $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================
log_step "1/10 - Pre-flight Checks"

# Check if .env exists
if [ ! -f ".env" ]; then
    log_error ".env file not found!"
    log_info "Creating from .env.example..."
    cp .env.example .env
    log_warning "Please edit .env with your credentials, then run again"
    exit 1
fi

# Load .env
export $(cat .env | grep -v '^#' | xargs)

# Validate required variables
if [ -z "$BOT_TOKEN" ]; then
    log_error "BOT_TOKEN not set in .env"
    exit 1
fi

if [ -z "$WEBHOOK_URL" ]; then
    log_error "WEBHOOK_URL not set in .env"
    exit 1
fi

if [ -z "$WEBHOOK_PATH" ]; then
    log_warning "WEBHOOK_PATH not set, using default: /webhook"
    echo "WEBHOOK_PATH=/webhook" >> .env
    export WEBHOOK_PATH="/webhook"
fi

# Extract domain from WEBHOOK_URL
DOMAIN=$(echo $WEBHOOK_URL | sed -e 's|^[^/]*//||' -e 's|/.*$||')

log_success "Configuration loaded"
log_info "Domain: $DOMAIN"
log_info "Webhook: $WEBHOOK_URL$WEBHOOK_PATH"
log_info "Bot Port: ${PORT:-8001}"

# Check for ngrok in URL
if echo "$WEBHOOK_URL" | grep -q "ngrok"; then
    log_error "ngrok detected in WEBHOOK_URL!"
    log_warning "For production, use your domain: https://$DOMAIN"
    log_warning "Update .env and run again"
    exit 1
fi

# ============================================================================
# BACKUP
# ============================================================================
log_step "2/10 - Creating Backup"

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/.env.backup"
    log_success ".env backed up"
fi

if [ -f "bot.log" ]; then
    cp bot.log "$BACKUP_DIR/bot.log.backup"
    log_success "bot.log backed up"
fi

log_success "Backup created: $BACKUP_DIR"

# ============================================================================
# STOP OLD PROCESSES
# ============================================================================
log_step "3/10 - Stopping Old Processes"

pkill -9 -f "uvicorn.*erpnext_bot" 2>/dev/null || true
pkill -9 -f "python.*app.webhook" 2>/dev/null || true
pkill -9 -f "python.*start_" 2>/dev/null || true
sleep 2

log_success "Old processes stopped"

# ============================================================================
# CLEAN CACHE
# ============================================================================
log_step "4/10 - Cleaning Python Cache"

find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

log_success "Python cache cleaned"

# ============================================================================
# GIT PULL (if in git repo)
# ============================================================================
log_step "5/10 - Updating Code"

if [ -d ".git" ]; then
    log_info "Git repository detected"
    git fetch origin
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    log_info "Current branch: $CURRENT_BRANCH"

    # Check if there are updates
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})

    if [ $LOCAL = $REMOTE ]; then
        log_info "Already up to date"
    else
        log_info "Pulling latest changes..."
        git pull origin $CURRENT_BRANCH
        log_success "Code updated"
    fi
else
    log_warning "Not a git repository, skipping update"
fi

# ============================================================================
# VIRTUAL ENVIRONMENT
# ============================================================================
log_step "6/10 - Setting Up Virtual Environment"

if [ ! -d ".venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv .venv
    log_success "Virtual environment created"
else
    log_info "Virtual environment exists"
fi

source .venv/bin/activate
log_success "Virtual environment activated"

# ============================================================================
# DEPENDENCIES
# ============================================================================
log_step "7/10 - Installing Dependencies"

.venv/bin/pip install --upgrade pip -q
if [ -f "requirements.txt" ]; then
    .venv/bin/pip install -r requirements.txt -q
    log_success "Dependencies installed"
else
    log_warning "requirements.txt not found"
fi

# ============================================================================
# TEST IMPORTS
# ============================================================================
log_step "8/10 - Testing Imports"

.venv/bin/python -B -c "
import sys
sys.dont_write_bytecode = True
try:
    from app.config import config
    from app.webhook.server import app
    print('✅ All imports OK')
    print(f'✅ Webhook will be set to: {config.telegram.webhook_url}{config.telegram.webhook_path}')
except Exception as e:
    print(f'❌ Import test failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" || {
    log_error "Import test failed!"
    exit 1
}

log_success "All imports successful"

# ============================================================================
# CHECK NGINX & SSL
# ============================================================================
log_step "9/10 - Checking Nginx & SSL"

# Check if nginx is installed
if ! command -v nginx &> /dev/null; then
    log_error "Nginx is not installed!"
    log_info "Run: sudo apt install nginx certbot python3-certbot-nginx"
    log_info "Or use: ./setup_nginx.sh"
    exit 1
fi

# Check if nginx is running
if ! systemctl is-active --quiet nginx; then
    log_warning "Nginx is not running"
    log_info "Starting nginx..."
    sudo systemctl start nginx
fi

log_success "Nginx is running"

# Check SSL certificate
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    log_success "SSL certificate found for $DOMAIN"

    # Check certificate expiry
    CERT_FILE="/etc/letsencrypt/live/$DOMAIN/cert.pem"
    if [ -f "$CERT_FILE" ]; then
        EXPIRY=$(sudo openssl x509 -enddate -noout -in "$CERT_FILE" | cut -d= -f2)
        log_info "Certificate expires: $EXPIRY"
    fi
else
    log_error "SSL certificate not found for $DOMAIN"
    log_info "Run: sudo certbot certonly --nginx -d $DOMAIN"
    log_info "Or use: ./setup_nginx.sh"
    exit 1
fi

# Check nginx configuration for this domain
NGINX_CONF="/etc/nginx/sites-available/$DOMAIN"
if [ -f "$NGINX_CONF" ]; then
    log_success "Nginx configuration found"

    # Test nginx config
    if sudo nginx -t 2>&1 | grep -q "successful"; then
        log_success "Nginx configuration valid"
    else
        log_error "Nginx configuration invalid!"
        sudo nginx -t
        exit 1
    fi
else
    log_error "Nginx configuration not found for $DOMAIN"
    log_info "Run: ./setup_nginx.sh"
    exit 1
fi

# ============================================================================
# START BOT
# ============================================================================
log_step "10/10 - Starting Bot"

# Check if port is in use
PORT=${PORT:-8001}
if lsof -ti:$PORT > /dev/null 2>&1; then
    log_warning "Port $PORT is in use, cleaning..."
    kill -9 $(lsof -ti:$PORT) 2>/dev/null || true
    sleep 2
fi

log_info "Starting bot on port $PORT..."

# Start bot with proper flags
PYTHONDONTWRITEBYTECODE=1 nohup .venv/bin/python -B -m uvicorn app.webhook.server:app \
  --host 0.0.0.0 \
  --port $PORT \
  --log-level info \
  > bot.log 2>&1 &

BOT_PID=$!
echo $BOT_PID > bot.pid

log_success "Bot started with PID: $BOT_PID"

# Wait for bot to start
log_info "Waiting for bot to initialize..."
sleep 5

# Check if bot is still running
if ps -p $BOT_PID > /dev/null; then
    log_success "Bot is running!"
else
    log_error "Bot failed to start!"
    log_info "Last 30 lines of log:"
    tail -30 bot.log
    exit 1
fi

# ============================================================================
# VERIFY WEBHOOK
# ============================================================================
log_info "Waiting for webhook to be set..."
sleep 3

log_info "Checking webhook status..."
WEBHOOK_INFO=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo")

if echo "$WEBHOOK_INFO" | grep -q "\"url\":\"$WEBHOOK_URL$WEBHOOK_PATH\""; then
    log_success "Webhook successfully set!"
else
    log_warning "Webhook may not be set correctly"
    log_info "Webhook info:"
    echo "$WEBHOOK_INFO" | python3 -m json.tool 2>/dev/null || echo "$WEBHOOK_INFO"
fi

# Test webhook endpoint
log_info "Testing webhook endpoint..."
if curl -s -k "https://$DOMAIN/" | grep -q "status"; then
    log_success "Webhook endpoint is accessible"
else
    log_warning "Could not reach webhook endpoint"
fi

# ============================================================================
# DEPLOYMENT COMPLETE
# ============================================================================
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   ✅ DEPLOYMENT SUCCESSFUL! ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}📊 System Status:${NC}"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "   Bot PID:        ${GREEN}$BOT_PID${NC}"
echo -e "   Port:           ${GREEN}$PORT${NC}"
echo -e "   Domain:         ${GREEN}$DOMAIN${NC}"
echo -e "   Webhook URL:    ${GREEN}$WEBHOOK_URL$WEBHOOK_PATH${NC}"
echo -e "   SSL:            ${GREEN}✅ Active${NC}"
echo -e "   Nginx:          ${GREEN}✅ Running${NC}"
echo ""
echo -e "${CYAN}🔧 Management:${NC}"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   View logs:       tail -f bot.log"
echo "   Nginx logs:      sudo tail -f /var/log/nginx/$DOMAIN.access.log"
echo "   Stop bot:        kill $BOT_PID"
echo "   Restart:         ./production_deploy.sh"
echo ""
echo -e "${CYAN}🧪 Testing:${NC}"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Webhook info:    curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
echo "   Test endpoint:   curl https://$DOMAIN/"
echo "   Test Telegram:   Send /start to your bot"
echo ""
echo -e "${YELLOW}📋 Recent Logs:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
tail -20 bot.log
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}🎉 Bot is ready! Test it on Telegram!${NC}"
echo ""
