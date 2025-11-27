#!/bin/bash
set -e

echo "============================="
echo "🚀 Starting ERPNextBot Deploy"
echo "============================="

### --- 1. CHECK REQUIRED COMMANDS --- ###
for cmd in python3 pip curl gunicorn; do
    if ! command -v $cmd &> /dev/null; then
        echo "❌ ERROR: '$cmd' not installed!"
        exit 1
    fi
done

### --- 2. LOAD ENV VARIABLES --- ###
if [ ! -f .env ]; then
    echo "❌ ERROR: .env not found!"
    exit 1
fi

export $(grep -v '^#' .env | xargs)

REQUIRED_VARS=(BOT_TOKEN WEBHOOK_URL WEBHOOK_PATH HOST PORT ERP_BASE_URL ERP_API_KEY ERP_API_SECRET)
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ ERROR: Missing required env variable: $var"
        exit 1
    fi
done

echo "📌 Loaded .env successfully!"

### --- 3. STOP OLD PROCESS --- ###
echo "🛑 Stopping old bot instance..."
PIDS=$(pgrep -f "gunicorn bot.main:app" || true)

if [ -n "$PIDS" ]; then
    echo "🔪 Killing: $PIDS"
    kill -9 $PIDS
else
    echo "⭕ No old bot found"
fi

sleep 1

### --- 4. CLEAR CACHE --- ###
echo "🧹 Clearing cache..."
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete

### --- 5. INSTALL DEPENDENCIES --- ###
echo "📦 Installing dependencies..."
pip install -r requirements.txt --quiet

### --- 6. CREATE LOGS --- ###
mkdir -p logs
LOG_FILE="logs/bot_$(date +%Y-%m-%d_%H-%M-%S).log"
touch $LOG_FILE

### --- 7. START BOT --- ###
echo "🚀 Starting bot with Gunicorn..."
nohup gunicorn bot.main:app \
    --bind $HOST:$PORT \
    --workers 1 \
    --timeout 120 \
    --log-level info \
    > $LOG_FILE 2>&1 &

sleep 2

### --- 8. SET WEBHOOK --- ###
echo "⚙️ Setting webhook: $WEBHOOK_URL$WEBHOOK_PATH"

WEBHOOK_RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
    -d "url=$WEBHOOK_URL$WEBHOOK_PATH")

echo $WEBHOOK_RESPONSE > logs/webhook_response.json

if echo "$WEBHOOK_RESPONSE" | grep -q '"ok":true'; then
    echo "✅ Webhook set successfully!"
else
    echo "❌ Webhook FAILED!"
    echo "👉 Check logs/webhook_response.json"
    exit 1
fi

echo "============================="
echo "🎉 DEPLOY SUCCESSFUL!"
echo "📄 Logs: $LOG_FILE"
echo "============================="
