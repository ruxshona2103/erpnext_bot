# 📋 SERVER COMMANDS - CHEAT SHEET

## 🚀 BIRINCHI MARTA SETUP

```bash
# 1. Serverga kirish
ssh your-server

# 2. Git pull
cd /path/to/erpnext_bot
git pull origin main

# 3. .env yaratish
cp .env.example .env
nano .env
# Ma'lumotlarni to'ldiring:
# BOT_TOKEN=8448405800:AAHmMWsabLpPz3IUl9zRrM3EBGM51MPWixg
# WEBHOOK_URL=https://bot.macone.net
# WEBHOOK_PATH=/webhook
# ERP_BASE_URL=https://macone.net
# ERP_API_KEY=f2890075f98bf32
# ERP_API_SECRET=5fcac2777ff2054

# 4. Scriptlarni executable qilish
chmod +x *.sh *.py

# 5. To'liq setup (faqat 1 marta!)
./setup_complete.sh
```

---

## 🔄 KEYINGI DEPLOYLAR

```bash
# Git pull
cd /path/to/erpnext_bot
git pull origin main

# Deploy
./production_deploy.sh
```

---

## 📊 MONITORING

```bash
# To'liq status
./check_status.sh

# Logs (real-time)
tail -f bot.log

# Nginx logs
sudo tail -f /var/log/nginx/bot.macone.net.access.log
sudo tail -f /var/log/nginx/bot.macone.net.error.log

# Bot process
ps aux | grep uvicorn

# Port
netstat -tulpn | grep 8001
```

---

## 🛠️ BOSHQARUV

```bash
# Restart
./production_deploy.sh

# Stop
kill $(cat bot.pid)

# Start
./production_deploy.sh

# Nginx restart
sudo systemctl restart nginx

# Nginx reload
sudo systemctl reload nginx
```

---

## 🧪 TEKSHIRISH

```bash
# Webhook info
curl https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo

# Endpoint test
curl https://bot.macone.net/

# Local endpoint
curl http://localhost:8001/

# SSL test
curl -I https://bot.macone.net/

# Nginx config test
sudo nginx -t

# SSL certificate
sudo certbot certificates
```

---

## 🔧 MUAMMOLARNI HAL QILISH

### Bot ishlamayapti
```bash
tail -50 bot.log
./production_deploy.sh
```

### Webhook xato
```bash
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
curl https://api.telegram.org/bot<TOKEN>/deleteWebhook
./production_deploy.sh
```

### Nginx muammosi
```bash
sudo nginx -t
sudo systemctl status nginx
sudo systemctl restart nginx
sudo tail -f /var/log/nginx/error.log
```

### Port band
```bash
lsof -i :8001
kill -9 $(lsof -ti:8001)
./production_deploy.sh
```

### SSL muammosi
```bash
sudo certbot certificates
sudo certbot renew
sudo systemctl reload nginx
```

---

## 📁 MUHIM FAYLLAR

```bash
# Konfiguratsiya
cat .env                    # Bot config
cat bot.log                 # Logs
cat bot.pid                 # Process ID

# Nginx
sudo cat /etc/nginx/sites-available/bot.macone.net
sudo cat /var/log/nginx/bot.macone.net.access.log

# SSL
sudo ls -la /etc/letsencrypt/live/bot.macone.net/
```

---

## 🔥 TEZKOR KOMANDALAR

```bash
# Setup (1 marta)
git pull && chmod +x *.sh && ./setup_complete.sh

# Deploy
git pull && ./production_deploy.sh

# Status
./check_status.sh

# Logs
tail -f bot.log

# Restart
kill $(cat bot.pid) && ./production_deploy.sh

# Full restart (Nginx + Bot)
sudo systemctl restart nginx && ./production_deploy.sh
```

---

## 📖 QOLLANMALAR

```bash
# Tezkor start
cat PRODUCTION_QUICKSTART.md

# To'liq overview
cat README_PRODUCTION.md

# Setup guide
cat WEBHOOK_SETUP.md
```

---

## ✅ CHECKLIST

Serverda ishga tushirishdan oldin:

- [ ] DNS configured: `bot.macone.net` → server IP
- [ ] Ports open: 80, 443
- [ ] Git pulled: `git pull origin main`
- [ ] .env created and filled
- [ ] Scripts executable: `chmod +x *.sh`
- [ ] Run setup: `./setup_complete.sh`
- [ ] Test bot: Send `/start`
- [ ] Check logs: `tail -f bot.log`

---

**Hammasi tayyor! 🎉**
