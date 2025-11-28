# 🚀 PRODUCTION QUICKSTART - BITTA BUYRUQ!

## ✅ MUAMMO YECHILDI!

**Muammo:** Bot lokalda ishlaydi (ngrok), serverda ishlamaydi
**Yechim:** Professional webhook with Nginx + SSL

---

## 📋 3 TA ODDIY QADAM

### QADAM 1: .env Sozlash

```bash
cd /home/your-username/erpnext_bot
nano .env
```

**Faqat shularni o'zgartiring:**
```bash
BOT_TOKEN=8448405800:AAHmMWsabLpPz3IUl9zRrM3EBGM51MPWixg
WEBHOOK_URL=https://bot.macone.net
WEBHOOK_PATH=/webhook

ERP_BASE_URL=https://macone.net
ERP_API_KEY=f2890075f98bf32
ERP_API_SECRET=5fcac2777ff2054
```

**Saqlab chiqing:** Ctrl+O, Enter, Ctrl+X

---

### QADAM 2: Birinchi Marta Setup (1 marta!)

```bash
./setup_complete.sh
```

**Bu script:**
- ✅ Nginx o'rnatadi
- ✅ SSL sertifikat oladi
- ✅ Nginx konfiguratsiya qiladi
- ✅ Botni ishga tushiradi
- ✅ Webhookni o'rnatadi

**Faqat 1 marta ishga tushirish kerak!**

---

### QADAM 3: Test Qilish

```bash
# 1. Status tekshirish
./check_status.sh

# 2. Telegram botga /start yuboring

# 3. Logs ko'rish
tail -f bot.log
```

---

## 🔄 KEYINGI DEPLOY'LAR

Keyinchalik kod o'zgartirganingizda:

```bash
./production_deploy.sh
```

Bu:
- ✅ Kodni git pull qiladi
- ✅ Botni restart qiladi
- ✅ Webhookni yangilaydi
- ✅ Tekshiradi va xabar beradi

**Nginx va SSL qayta sozlamaydi - ular allaqachon ishlaydi!**

---

## 📊 TIZIM QANDAY ISHLAYDI?

```
┌──────────┐    HTTPS     ┌───────┐   Proxy   ┌──────┐
│ Telegram │ ──────────▶  │ Nginx │ ────────▶ │ Bot  │
│          │ bot.macone   │ :443  │  :8001    │Python│
└──────────┘   .net       └───────┘           └──────┘
                  │
                  │ SSL
                  ▼
           Let's Encrypt
```

**Workflow:**
1. Telegram → `https://bot.macone.net/webhook` (HTTPS)
2. Nginx → `http://localhost:8001/webhook` (reverse proxy)
3. Bot → Update qabul qiladi va javob beradi

---

## 🛠️ BOSHQARUV BUYRUQLARI

```bash
# Status tekshirish
./check_status.sh

# Bot restart
./production_deploy.sh

# Logs (real-time)
tail -f bot.log

# Nginx logs
sudo tail -f /var/log/nginx/bot.macone.net.access.log

# Bot to'xtatish
kill $(cat bot.pid)

# Nginx restart
sudo systemctl restart nginx
```

---

## 🧪 TEKSHIRISH

### 1. Bot ishlayaptimi?

```bash
./check_status.sh
```

**Natija:**
```
✅ Bot Process: Running (PID: 12345)
✅ Port 8001: Running
✅ Nginx: Running
✅ SSL Certificate: Valid (expires in 89 days)
✅ Webhook: Set to https://bot.macone.net/webhook
✅ Endpoint: Accessible
```

### 2. Webhook o'rnatildimi?

```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo
```

**Kutilgan natija:**
```json
{
  "ok": true,
  "result": {
    "url": "https://bot.macone.net/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

### 3. HTTPS ishlayaptimi?

```bash
curl https://bot.macone.net/
```

**Natija:**
```json
{"status":"ok","message":"Webhook server is running"}
```

---

## ❌ MUAMMOLAR

### Bot ishlamayapti

```bash
# Logs tekshirish
tail -50 bot.log

# Restart
./production_deploy.sh
```

### Webhook xato

```bash
# Webhook info
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo

# Delete va restart
curl https://api.telegram.org/bot<TOKEN>/deleteWebhook
./production_deploy.sh
```

### Nginx xato

```bash
# Nginx status
sudo systemctl status nginx

# Test config
sudo nginx -t

# Restart
sudo systemctl restart nginx
```

### SSL muammosi

```bash
# SSL tekshirish
sudo certbot certificates

# Yangilash
sudo certbot renew
sudo systemctl reload nginx
```

---

## 📁 FAYLLAR TUZILISHI

```
erpnext_bot/
├── setup_complete.sh       ← BIRINCHI MARTA (Nginx + SSL + Bot)
├── production_deploy.sh    ← KEYINGI DEPLOY'LAR
├── check_status.sh         ← STATUS TEKSHIRISH
├── .env                    ← KONFIGURATSIYA
├── bot.log                 ← LOGS
├── bot.pid                 ← PROCESS ID
└── app/                    ← BOT KODI
```

---

## ⚡ TEZKOR KOMANDALAR

```bash
# Birinchi marta setup
./setup_complete.sh

# Har safar deploy
./production_deploy.sh

# Status
./check_status.sh

# Logs
tail -f bot.log

# Restart
kill $(cat bot.pid) && ./production_deploy.sh
```

---

## 🎯 ASOSIY FARQLAR

### Eski (ngrok):
```bash
❌ Har safar yangi URL
❌ Terminal yopilsa o'chadi
❌ Professional emas
❌ Localhost uchun
```

### Yangi (Production):
```bash
✅ Doimiy URL (bot.macone.net)
✅ 24/7 ishlaydi
✅ Professional + Xavfsiz
✅ Production server uchun
✅ SSL + Nginx
✅ Bir buyruq deploy
```

---

## 📞 YORDAM

**Tezkor tekshirish:**
```bash
./check_status.sh
```

**To'liq deploy:**
```bash
./production_deploy.sh
```

**Muammo bo'lsa:**
1. `tail -f bot.log` - bot logs
2. `sudo tail -f /var/log/nginx/bot.macone.net.error.log` - nginx logs
3. `./check_status.sh` - system status

---

## ✅ XULOSA

**3 ta oddiy buyruq:**

```bash
# 1. .env sozlash (bitta marta)
nano .env

# 2. To'liq setup (bitta marta)
./setup_complete.sh

# 3. Keyingi deploy'lar
./production_deploy.sh
```

**Hammasi tayyor! Professional, ishonchli, xavfsiz! 🎉**

---

## 🔥 BONUS: Auto-Restart (systemd)

Serverda avtomatik restart uchun:

```bash
sudo nano /etc/systemd/system/erpnext-bot.service
```

```ini
[Unit]
Description=ERPNext Telegram Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/erpnext_bot
ExecStart=/home/your-username/erpnext_bot/.venv/bin/python -m uvicorn app.webhook.server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Yoqish
sudo systemctl daemon-reload
sudo systemctl enable erpnext-bot
sudo systemctl start erpnext-bot

# Status
sudo systemctl status erpnext-bot
```

**Endi server restart bo'lsa ham bot avtomatik ishga tushadi! ✅**
