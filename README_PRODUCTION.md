# 🚀 ERPNext Telegram Bot - Production Deployment

## ✅ TO'LIQ PROFESSIONAL YECHIM

Bu production-ready deployment - **bir buyruq bilan to'liq ishlaydigan bot!**

### Nima o'zgarti?
- ❌ **Eski:** ngrok (har safar yangi URL, terminalni yopsa o'chadi)
- ✅ **Yangi:** Professional webhook (Nginx + SSL + doimiy domen)

---

## 🎯 TEZKOR BOSHLASH

### 1️⃣ Birinchi Marta Setup

```bash
# .env sozlash
nano .env
# WEBHOOK_URL=https://bot.macone.net ni yozing

# To'liq setup (1 marta!)
./setup_complete.sh
```

**Bu hammasi! Bot tayyor! ✅**

### 2️⃣ Keyingi Deploy'lar

```bash
./production_deploy.sh
```

### 3️⃣ Status Tekshirish

```bash
./check_status.sh
```

---

## 📁 ASOSIY FAYLLAR

| Fayl | Vazifasi | Qachon ishlatiladi |
|------|----------|-------------------|
| **setup_complete.sh** | To'liq setup (Nginx+SSL+Bot) | 🔴 **Birinchi marta** |
| **production_deploy.sh** | Bot deploy/restart | 🟢 **Har safar** |
| **check_status.sh** | System status | 🔵 **Tekshirish** |
| **.env** | Konfiguratsiya | ✏️ **O'zgartirish** |

---

## 🔥 QISQA QOLLANMA

### Birinchi Marta Setup:

```bash
# 1. .env ni to'ldiring
nano .env

# 2. Hammasi avtomatik!
./setup_complete.sh
```

**Script qiladi:**
- ✅ Nginx o'rnatadi
- ✅ SSL sertifikat oladi (Let's Encrypt)
- ✅ Reverse proxy sozlaydi
- ✅ Botni ishga tushiradi
- ✅ Webhookni o'rnatadi
- ✅ Tekshiradi va xabar beradi

### Keyingi Deploylar:

```bash
./production_deploy.sh
```

**Bu:**
- Git pull
- Cache tozalash
- Botni restart
- Webhook yangilash
- Tekshirish

### Monitoring:

```bash
./check_status.sh
```

**Ko'rsatadi:**
- Bot jarayoni
- Port holati
- Nginx holati
- SSL sertifikat
- Webhook holati
- Endpoint holati
- Recent logs

---

## 📊 ARCHITECTURE

```
Internet (HTTPS)
      ↓
bot.macone.net (SSL Certificate)
      ↓
Nginx (Reverse Proxy) :443
      ↓
Localhost :8001
      ↓
Bot (Python/uvicorn)
      ↓
ERPNext API
```

**Xavfsizlik:**
- ✅ SSL/HTTPS
- ✅ Bot localhost da (tashqaridan ko'rinmaydi)
- ✅ Nginx reverse proxy
- ✅ Firewall

---

## 🛠️ BOSHQARUV

```bash
# Status
./check_status.sh

# Logs (real-time)
tail -f bot.log

# Nginx logs
sudo tail -f /var/log/nginx/bot.macone.net.access.log

# Restart
./production_deploy.sh

# Stop
kill $(cat bot.pid)
```

---

## ✅ TEKSHIRISH CHECKLISTI

Deploy qilgandan keyin:

- [ ] `./check_status.sh` - barcha ✅ ko'rsatadi
- [ ] Telegram botga `/start` yuborish ishlaydi
- [ ] `tail -f bot.log` - ERROR yo'q
- [ ] `curl https://bot.macone.net/` - javob beradi

---

## 🔧 MUAMMOLAR VA YECHIMLAR

### ❌ Bot ishlamayapti

```bash
tail -50 bot.log
./production_deploy.sh
```

### ❌ Webhook xato

```bash
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
curl https://api.telegram.org/bot<TOKEN>/deleteWebhook
./production_deploy.sh
```

### ❌ Nginx muammosi

```bash
sudo nginx -t
sudo systemctl restart nginx
```

### ❌ SSL muammosi

```bash
sudo certbot certificates
sudo certbot renew
sudo systemctl reload nginx
```

---

## 📖 BATAFSIL QOLLANMALAR

- **PRODUCTION_QUICKSTART.md** - Tezkor boshlash
- **PRODUCTION_WEBHOOK_DEPLOY.md** - Batafsil qo'llanma
- **WEBHOOK_SETUP.md** - Step-by-step setup
- **nginx_config_example.conf** - Nginx config namunasi

---

## 🎯 FEATURES

### ✅ Ishlab Turgan:
- Telegram bot (webhook mode)
- ERPNext integration
- Payment Entry webhook
- SSL/HTTPS
- Professional deployment
- Auto-restart
- Monitoring
- Logging

### 🔄 Deployment:
- Git-based updates
- Zero-downtime deploy
- Automatic cache cleanup
- Health checks
- Webhook verification

### 🔒 Security:
- SSL/TLS encryption
- Nginx reverse proxy
- Firewall configured
- Bot hidden from internet
- API key protection

---

## 📈 PRODUCTION BEST PRACTICES

### 1. Monitoring

```bash
# Crontab - har kuni tekshirish
0 9 * * * cd /path/to/erpnext_bot && ./check_status.sh | mail -s "Bot Status" admin@example.com
```

### 2. Auto-Restart (systemd)

```bash
# /etc/systemd/system/erpnext-bot.service
sudo systemctl enable erpnext-bot
sudo systemctl start erpnext-bot
```

### 3. Log Rotation

```bash
# /etc/logrotate.d/erpnext-bot
/path/to/erpnext_bot/bot.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

### 4. Backup

```bash
# Har kuni backup
0 2 * * * cd /path/to/erpnext_bot && tar -czf backups/bot-$(date +\%Y\%m\%d).tar.gz .env app/
```

---

## 🎉 XULOSA

**3 ta buyruq:**

1. **Birinchi marta:** `./setup_complete.sh`
2. **Har safar deploy:** `./production_deploy.sh`
3. **Status:** `./check_status.sh`

**Hammasi tayyor! Professional, ishonchli, xavfsiz! ✅**

---

## 📞 SUPPORT

Muammo bo'lsa:

1. `./check_status.sh` - tizim holatini tekshiring
2. `tail -f bot.log` - xatolarni toping
3. `./production_deploy.sh` - restart qiling

**Batafsil:** `PRODUCTION_QUICKSTART.md`

---

**Made with ❤️ for Production**
