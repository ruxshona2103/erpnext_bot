# 🚀 WEBHOOK SETUP - QISQA QOLLANMA

## ❓ Sizning muammongiz

**Lokalda:** Bot ishlaydi (ngrok bilan)
**Serverda:** Bot ishlamaydi (ngrok o'chadi)

**Sabab:** `.env` da `WEBHOOK_URL=https://ngrok...` yozilgan

---

## ✅ YECHIM: Production Webhook (Domen bilan)

Sizda: `https://bot.macone.net` domeni bor ✅

---

## 📋 3 TA ODDIY QADAM

### 1️⃣ Nginx + SSL sozlash (birinchi marta)

```bash
# Serverda
cd /home/your-username/erpnext_bot
./setup_nginx.sh
```

**Script so'raydi:**
- Domen: `bot.macone.net` (kiriting)

**Script qiladi:**
- ✅ Nginx o'rnatadi
- ✅ SSL sertifikat oladi (Let's Encrypt)
- ✅ Nginx konfiguratsiya yaratadi
- ✅ Firewall ochadi

**1 marta bajarish yetarli!**

---

### 2️⃣ .env faylni sozlash

```bash
nano .env
```

**O'zgartiring:**
```bash
# Eski (ngrok):
WEBHOOK_URL=https://ngrok-random-url.ngrok-free.dev  ❌

# Yangi (domen):
WEBHOOK_URL=https://bot.macone.net  ✅
WEBHOOK_PATH=/webhook               ✅
```

**Saqlab chiqing:** `Ctrl+O`, `Enter`, `Ctrl+X`

---

### 3️⃣ Botni deploy qilish

```bash
./deploy.sh
```

**Tayyor! Bot webhook rejimida ishlaydi.**

---

## 🔍 TEKSHIRISH

```bash
# 1. Bot ishlayaptimi?
ps aux | grep uvicorn

# 2. Nginx ishlayaptimi?
sudo systemctl status nginx

# 3. Webhook o'rnatildimi?
curl https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo
```

**Natija:**
```json
{
  "ok": true,
  "result": {
    "url": "https://bot.macone.net/webhook",
    "pending_update_count": 0
  }
}
```

---

## 🔄 RESTART

```bash
# Bot restart
pkill -f uvicorn
./deploy.sh

# Nginx restart (kerak bo'lsa)
sudo systemctl reload nginx
```

---

## 📊 QANDAY ISHLAYDI?

```
┌─────────┐      HTTPS      ┌──────────┐     Proxy      ┌─────────┐
│ Telegram│ ───────────────▶ │  Nginx   │ ─────────────▶ │   Bot   │
│         │  bot.macone.net  │  (SSL)   │  localhost:8001│ (Python)│
└─────────┘                  └──────────┘                └─────────┘
```

1. Telegram → `https://bot.macone.net/webhook`
2. Nginx → `http://localhost:8001/webhook`
3. Bot update qabul qiladi

---

## 🛠️ MUAMMOLAR

### ❌ "SSL verify failed"

```bash
# SSL tekshirish
sudo certbot certificates

# SSL yangilash
sudo certbot renew
sudo systemctl reload nginx
```

### ❌ Bot javob bermaydi

```bash
# Logs
tail -50 bot.log
sudo tail -50 /var/log/nginx/bot.macone.net.error.log

# Restart
pkill -f uvicorn
./deploy.sh
```

### ❌ "Connection refused"

```bash
# Port tekshirish
netstat -tulpn | grep 8001

# Bot ishga tushirish
./deploy.sh
```

---

## 📁 FAYLLAR

| Fayl | Tavsif |
|------|--------|
| `setup_nginx.sh` | Nginx + SSL sozlash (1 marta) |
| `deploy.sh` | Botni deploy qilish |
| `.env` | Konfiguratsiya (WEBHOOK_URL o'zgartiring!) |
| `PRODUCTION_WEBHOOK_DEPLOY.md` | Batafsil qo'llanma |
| `nginx_config_example.conf` | Nginx config namunasi |

---

## ⚡ TEZKOR SETUP

```bash
# 1. Serverda (birinchi marta)
./setup_nginx.sh
# Domain: bot.macone.net

# 2. .env sozlash
nano .env
# WEBHOOK_URL=https://bot.macone.net
# WEBHOOK_PATH=/webhook

# 3. Deploy
./deploy.sh

# 4. Test
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
```

**3 daqiqa ichida tayyor! 🎉**

---

## 🆚 NGROK vs PRODUCTION

| Feature | NGROK | Production |
|---------|-------|------------|
| URL | Har safar o'zgaradi | Doimiy |
| Ishonchlilik | Terminal yopilsa o'chadi | 24/7 |
| SSL | Avtomatik | Let's Encrypt (tekin) |
| Narx | Tekin (cheklangan) | Server narxi |

**Production = Ishonchli + Professional! ✅**

---

## 📞 YORDAM

**Qisqa:**
```bash
# Logs
tail -f bot.log

# Status
ps aux | grep uvicorn
sudo systemctl status nginx

# Restart
./deploy.sh
```

**Batafsil qo'llanma:**
```bash
cat PRODUCTION_WEBHOOK_DEPLOY.md
```

**Hammasi tayyor! 🚀**
