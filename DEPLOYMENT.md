# 🚀 ERPNext Bot - Deployment Guide

## Quick Manual Deployment

### Local mashinada (testing):

```bash
cd /home/user/Documents/erpnext_bot
./deploy_improved.sh
```

### Serverdagi bot uchun (production):

SSH orqali serverga kiring va:

```bash
ssh root@SERVER_IP
cd /root/erpnext_bot
./deploy_improved.sh
```

---

## 📋 Deployment Status Tekshirish

Hozirgi holatni tekshirish uchun:

```bash
./check_deployment.sh
```

Bu script quyidagilarni tekshiradi:
- ✅ Bot process ishlayaptimi
- ✅ Kod eng oxirgi versiyami
- ✅ Git remote bilan sync holati
- ✅ Log fayllarida xatoliklar
- ✅ Zarur fayllar mavjudmi

---

## 🔄 CI/CD va Qo'lda Deploy

### CI/CD (Avtomatik) - GitHub Actions

Har safar `main` branchga push qilganingizda:

```bash
git add .
git commit -m "O'zgarish tavsifi"
git push origin main
```

GitHub Actions avtomatik ravishda:
1. Serverdagi `/root/erpnext_bot` papkasiga SSH ulanadi
2. Git'dan yangi kodni tortadi
3. `./deploy_polling.sh` ni ishga tushiradi
4. Botni qayta ishga tushiradi

**Muammo:** Ba'zan CI/CD ishlaydi, lekin bot **yangi kodga o'tmaydi** - chunki:
- Python import cache tozalanmaydi
- Process to'xtalmaydi yoki eski kod bilan ishga tushadi

### Qo'lda Deploy (Ishonchli)

Agar CI/CD ishlamasa yoki tez deploy kerak bo'lsa:

```bash
# 1. Serverga kiring
ssh root@SERVER_IP

# 2. Bot papkasiga o'ting
cd /root/erpnext_bot

# 3. Yangi kodni torting
git pull origin main

# 4. Yaxshilangan deploy scriptni ishga tushiring
./deploy_improved.sh
```

---

## 🛠️ Deploy Scriptlar Farqi

| Script | Vazifasi | Qachon ishlatish |
|--------|----------|------------------|
| `deploy_polling.sh` | Standart deploy | CI/CD ishlatadi |
| `deploy_improved.sh` | Yaxshilangan deploy | Qo'lda deploy uchun tavsiya etiladi |
| `check_deployment.sh` | Diagnostika | Holatni tekshirish |

### `deploy_improved.sh` ning afzalliklari:

1. **Graceful shutdown** - Avval SIGTERM, keyin SIGKILL
2. **Aggressive cache cleaning** - Barcha Python cache'ni tozalaydi
3. **Better verification** - Git commit, logs, process statusini ko'rsatadi
4. **No cache flags** - `PYTHONDONTWRITEBYTECODE=1` bilan ishga tushadi

---

## 🔍 Muammolarni Tuzatish

### Muammo 1: O'zgarishlar botda ko'rinmayapti

**Sabab:** Python import cache yoki eski process

**Yechim:**
```bash
ssh root@SERVER_IP
cd /root/erpnext_bot
./deploy_improved.sh
```

### Muammo 2: Bot ishga tushmayapti

**Sabab:** .env fayl yo'q yoki token noto'g'ri

**Yechim:**
```bash
# Serverdagi .env faylini tekshiring
ssh root@SERVER_IP
cat /root/erpnext_bot/.env

# BOT_TOKEN to'g'ri ekanligini tasdiqlang
```

### Muammo 3: CI/CD ishlamayapti

**Sabab:** GitHub Secrets noto'g'ri

**Yechim:**

GitHub → Settings → Secrets → Actions → Quyidagilarni tekshiring:
- `SERVER_IP` - Server IP manzili
- `SSH_PRIVATE_KEY` - SSH private key (root user uchun)

### Muammo 4: Commands menyuda ko'rinmayapti

**Sabab:** Telegram commandlar menyusi yangilanmagan

**Yechim 1 (Kod orqali):**
```bash
cd /home/user/Documents/erpnext_bot
.venv/bin/python set_bot_commands.py
```

**Yechim 2 (BotFather orqali):**
1. Telegram'da `@BotFather` ga `/mybots` yozing
2. O'z botingizni tanlang
3. Edit Bot → Edit Commands
4. Quyidagini yuboring:
```
start - Botni boshlash
help - Yordam va operator raqami
```

---

## 📊 Log Fayllarni Ko'rish

### Real-time logs:
```bash
tail -f /root/erpnext_bot/bot_polling.log
```

### Oxirgi 50 qator:
```bash
tail -50 /root/erpnext_bot/bot_polling.log
```

### Xatoliklarni qidirish:
```bash
grep -i "error\|exception" /root/erpnext_bot/bot_polling.log | tail -20
```

---

## 🎯 Deployment Checklist

Har safar deploy qilishdan oldin:

- [ ] Local mashinada test qilganmisiz?
- [ ] Git'ga commit qilganmisiz?
- [ ] Commit message aniq va tushunarli?
- [ ] GitHub'ga push qilganmisiz?
- [ ] CI/CD Actions'da success bo'lganmi? (https://github.com/ruxshona2103/erpnext_bot/actions)
- [ ] Serverdagi bot yangilanganmi? (`./check_deployment.sh`)
- [ ] Telegram'da botni test qilganmisiz?

---

## 📞 Deployment Muammolari

Agar qo'lda deploy ham ishlamasa:

1. Process'larni to'xtatish:
```bash
pkill -9 -f start_polling_bot
pkill -9 -f "python.*erpnext"
```

2. Cache'ni tozalash:
```bash
find /root/erpnext_bot -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find /root/erpnext_bot -type f -name "*.pyc" -delete 2>/dev/null
```

3. Botni qayta ishga tushirish:
```bash
cd /root/erpnext_bot
./deploy_improved.sh
```

---

## ✅ Senior-Level Tavsiyalar

1. **Har doim `deploy_improved.sh` ishlatish** - Bu script cache va process muammolarini hal qiladi
2. **`check_deployment.sh` ni doimiy tekshirish** - Deployment holatini monitoring qilish
3. **CI/CD'ga ishonmang** - Har doim qo'lda verify qiling
4. **Logs'ni tekshiring** - `tail -f bot_polling.log` bilan real-time ko'ring
5. **BotFather orqali commands sozlang** - Bu eng ishonchli usul

---

**Yaratilgan:** 2025-12-02
**Muallif:** Claude Code + ruxshona2103
