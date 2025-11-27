#!/bin/bash
# Cache tozalash va restart

set -e

echo "🧹 CACHE TOZALASH VA RESTART"
echo "======================================"

cd /home/ruxshona/Documents/erpnext_bot

# 1. BARCHA PROCESS'LARNI TO'XTATISH
echo "1️⃣ Bot process'larni to'xtatish..."
pkill -9 -f "uvicorn.*erpnext_bot" 2>/dev/null || true
pkill -9 -f "python.*app.webhook" 2>/dev/null || true
sleep 2

# 2. PYTHON CACHE TOZALASH
echo "2️⃣ Python cache tozalash..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "   ✅ Cache tozalandi"

# 3. GIT PULL (har ehtimolga qarshi)
echo "3️⃣ Yangi kod olish..."
git fetch origin
git reset --hard origin/main
echo "   ✅ Kod yangilandi"

# 4. IMPORTLARNI TEST QILISH
echo "4️⃣ Importlarni test qilish..."
.venv/bin/python -c "
import sys
sys.dont_write_bytecode = True  # .pyc yaratmaslik
from app.services.support import get_support_contact_sync
from app.handlers.passport import passport_input_handler
from app.config import config
print(f'   ✅ Support phone: {config.support.phone}')
contact = get_support_contact_sync()
print(f'   ✅ Contact: {contact}')
" || { echo "❌ Import test xato berdi!"; exit 1; }

# 5. PORT TEKSHIRISH
echo "5️⃣ Port 8001 tekshirish..."
if lsof -ti:8001 > /dev/null 2>&1; then
    echo "   ⚠️ Port band, tozalanmoqda..."
    kill -9 $(lsof -ti:8001) 2>/dev/null || true
    sleep 2
fi

# 6. BOT'NI ISHGA TUSHIRISH (bytecode yozmasdan)
echo "6️⃣ Bot ishga tushmoqda..."
PYTHONDONTWRITEBYTECODE=1 nohup .venv/bin/python -B -m uvicorn app.webhook.server:app \
  --host 0.0.0.0 \
  --port 8001 \
  --reload \
  > bot.log 2>&1 &

BOT_PID=$!
echo "   ✅ Bot PID: $BOT_PID"

# 7. LOG KUTISH
echo "7️⃣ Bot log tekshirmoqda (5 sekund)..."
sleep 5

echo ""
echo "======================================"
echo "📊 BOT LOG (oxirgi 30 qator):"
echo "======================================"
tail -30 bot.log

echo ""
echo "======================================"
echo "✅ TAYYOR!"
echo "======================================"
echo "🔍 Process: ps aux | grep uvicorn"
echo "📊 Log: tail -f bot.log"
echo "🧪 Test: Telegram'da passport kiriting"
echo "======================================"
