# 🔧 Server Deploy Muammolarini Yechish

## ❓ Muammo: Lokal ishlaydi, serverda ishlamaydi

### 🎯 TEKSHIRISH QADAMLARI:

## 1️⃣ Server Kodini Yangilang

```bash
# Serverga SSH
ssh user@server-ip

# Bot papkasiga o'ting
cd /home/ruxshona/Documents/erpnext_bot

# Git pull qiling
git pull origin main

# Yangilangan fayllarni ko'ring
git log -1 --stat
```

---

## 2️⃣ .env Faylni Tekshiring

```bash
# .env faylda SUPPORT qatorlari bormi?
cat .env | grep SUPPORT

# Agar yo'q bo'lsa, qo'shing:
nano .env
```

`.env` ga qo'shing:
```bash
SUPPORT_PHONE=+998 99 123 45 67
SUPPORT_NAME=Operator
```

---

## 3️⃣ Python Dependencies Tekshirish

```bash
# Virtual environment aktivlash
cd /home/ruxshona/Documents/erpnext_bot
source .venv/bin/activate

# Yangi dependencies bormi?
pip list | grep -i httpx
pip list | grep -i tenacity
```

---

## 4️⃣ Modullarni Test Qiling

```bash
# Support service import test
.venv/bin/python -c "
from app.services.support import get_support_contact_sync
contact = get_support_contact_sync()
print('✅ Support service ishlaydi')
print(f'Contact: {contact}')
"

# Agar xato bo'lsa, xatoni ko'rsatadi
```

---

## 5️⃣ Bot Process'ini To'liq Restart Qiling

### A. Eski process'ni to'xtating

```bash
# Bot process'ini topish
ps aux | grep uvicorn

# Yoki
ps aux | grep python | grep erpnext_bot

# Process'ni o'chirish
kill -9 <PROCESS_ID>

# Yoki hamma python process'larni to'xtatish
pkill -f "uvicorn.*erpnext_bot"
```

### B. Yangi process'ni ishga tushiring

```bash
cd /home/ruxshona/Documents/erpnext_bot

# Virtual environment aktivlash
source .venv/bin/activate

# Bot ishga tushirish
nohup .venv/bin/python -m uvicorn app.webhook.server:app \
  --host 0.0.0.0 --port 8001 > bot.log 2>&1 &

# Yoki systemd service bo'lsa:
sudo systemctl restart erpnext-bot
```

---

## 6️⃣ Log'larni Tekshiring

```bash
# Bot log'ini ko'rish
tail -f /home/ruxshona/Documents/erpnext_bot/bot.log

# Yoki
tail -f /home/ruxshona/Documents/erpnext_bot/logs/bot.log

# Quyidagilarni qidiring:
# ✅ Support contact loaded: ...
# ❌ Support contact loading failed: ...
```

---

## 7️⃣ Config Yuklashni Test Qiling

```bash
cd /home/ruxshona/Documents/erpnext_bot

.venv/bin/python -c "
from app.config import config
print('✅ Config loaded')
print(f'Support phone: {config.support.phone}')
print(f'Support name: {config.support.operator_name}')
"
```

---

## 8️⃣ Import Error'larni Tekshiring

```bash
# Barcha fayllarni import test
.venv/bin/python -c "
from app.handlers import passport, start, reminders_handler, payments
from app.services import support, erpnext_api
from app.utils import formatters
print('✅ Barcha modullar import qilindi')
"
```

---

## 🐛 ENG KO'P UCHRAYDIGAN MUAMMOLAR:

### ❌ Muammo 1: ModuleNotFoundError: app.services.support

**Sabab:** git pull qilinmagan yoki fayl ko'chirilmagan

**Yechim:**
```bash
cd /home/ruxshona/Documents/erpnext_bot
git pull origin main
ls -la app/services/support.py  # Fayl borligini tekshiring
```

---

### ❌ Muammo 2: KeyError: 'support'

**Sabab:** .env faylda SUPPORT_PHONE yo'q

**Yechim:**
```bash
echo "SUPPORT_PHONE=+998 99 123 45 67" >> .env
echo "SUPPORT_NAME=Operator" >> .env
```

---

### ❌ Muammo 3: Bot eski versiyada ishlayapti

**Sabab:** Process restart qilinmagan

**Yechim:**
```bash
# Process'ni to'xtating
pkill -f uvicorn

# Qaytadan ishga tushiring
cd /home/ruxshona/Documents/erpnext_bot
.venv/bin/python -m uvicorn app.webhook.server:app --host 0.0.0.0 --port 8001
```

---

### ❌ Muammo 4: ERPNext API ishlamayapti

**Sabab:** cash_flow_app ga API qo'shilmagan

**Yechim:**
Bu muammo emas! Fallback ishlaydi:
- ERPNext'dan olmasa, .env fayldagi SUPPORT_PHONE ishlatadi
- Xato xabar baribir ko'rsatiladi

---

## ✅ TO'LIQ DEPLOY SCRIPT:

```bash
#!/bin/bash
# Server Deploy Script

echo "🚀 Bot serverga deploy qilish..."

cd /home/ruxshona/Documents/erpnext_bot

# 1. Git pull
echo "📥 Yangi kod olish..."
git pull origin main

# 2. .env tekshirish
if ! grep -q "SUPPORT_PHONE" .env; then
    echo "📝 .env ga SUPPORT qo'shilmoqda..."
    echo "" >> .env
    echo "# Support Configuration" >> .env
    echo "SUPPORT_PHONE=+998 99 123 45 67" >> .env
    echo "SUPPORT_NAME=Operator" >> .env
fi

# 3. Dependencies yangilash (agar kerak bo'lsa)
source .venv/bin/activate
# pip install -r requirements.txt --upgrade

# 4. Test
echo "🧪 Modullarni test qilish..."
.venv/bin/python -c "from app.services.support import get_support_contact_sync; print('✅ OK')" || exit 1

# 5. Process restart
echo "🔄 Bot'ni qaytadan ishga tushirish..."
pkill -f "uvicorn.*erpnext_bot"
sleep 2

nohup .venv/bin/python -m uvicorn app.webhook.server:app \
  --host 0.0.0.0 --port 8001 > bot.log 2>&1 &

echo "✅ Deploy tugadi!"
echo "📊 Log: tail -f bot.log"
```

Saqlang: `deploy.sh`
Ishlatish:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 📞 QISQA YECHIM:

```bash
# Serverda
cd /home/ruxshona/Documents/erpnext_bot
git pull
pkill -f uvicorn
source .venv/bin/activate
.venv/bin/python -m uvicorn app.webhook.server:app --host 0.0.0.0 --port 8001
```

Bu ishlashi kerak! ✅
