# 🔧 Troubleshooting Guide - O'zgarishlar nima uchun ko'rinmayapti?

## Muammoni topish uchun qadamlar:

### 1️⃣ Debug scriptni ishga tushiring

Serverdagi botni tekshirish uchun:

```bash
ssh root@SERVER_IP
cd /root/erpnext_bot
./debug_bot.sh
```

Bu script quyidagilarni tekshiradi:
- ✅ Kod versiyasi (qaysi commit ishlamoqda)
- ✅ /help command kodi mavjudmi
- ✅ Bot process ishlayaptimi
- ✅ Python cache mavjudmi
- ✅ Loglarida xatolik bormi
- ✅ Code fayllar qachon o'zgartirilgan
- ✅ Process qachon ishga tushgan

---

## Muammolar va Yechimlar

### ❌ MUAMMO 1: Python cache eski kod ishlatadi

**Belgisi:**
```
⚠️  WARNING: Python cache exists!
   .pyc files: 400+
   __pycache__ dirs: 50+
```

**Sabab:** Python import cache'da eski kod saqlangan

**Yechim:**
```bash
# Cache'ni tozalash
find . -name '*.pyc' -delete
find . -name '__pycache__' -exec rm -rf {} +

# Botni qayta ishga tushirish
./deploy_improved.sh
```

---

### ❌ MUAMMO 2: Bot eski code bilan ishlamoqda

**Belgisi:**
```
❌ MUAMMO: Kod yangilangan, lekin bot qayta ishga tushmagan
   Fayl yangilangan: 2025-12-02 14:00
   Process boshlangan: 2025-12-02 10:00
```

**Sabab:** Git pull qilindi, lekin bot process restart bo'lmadi

**Yechim:**
```bash
# Botni majburan to'xtatish
pkill -9 -f start_polling_bot
pkill -9 -f "python.*erpnext"

# Cache tozalash
find . -name '*.pyc' -delete
find . -name '__pycache__' -exec rm -rf {} +

# Qayta ishga tushirish
./deploy_improved.sh
```

---

### ❌ MUAMMO 3: /help command kodi mavjud emas

**Belgisi:**
```
❌ /help command code NOT FOUND in app/handlers/start.py
```

**Sabab:** Git pull ishlamagan yoki branch noto'g'ri

**Yechim:**
```bash
# Current branch va commitni tekshiring
git status
git log --oneline -3

# Agar kerak bo'lsa, pull qiling
git pull origin main

# Force update
git fetch origin main
git reset --hard origin/main

# Deploy
./deploy_improved.sh
```

---

### ❌ MUAMMO 4: Bot token noto'g'ri

**Belgisi:**
```
TelegramUnauthorizedError: Telegram server says - Unauthorized
```

**Sabab:** .env fayldagi BOT_TOKEN noto'g'ri yoki eskirgan

**Yechim:**
```bash
# .env faylni tekshiring
cat .env | grep BOT_TOKEN

# BotFather'dan yangi token oling va .env'ni yangilang
nano .env
```

---

### ❌ MUAMMO 5: Commands menyuda ko'rinmayapti

**Belgisi:** Bot ishlayapti, /help command javob beradi, lekin Telegram menyusida ko'rinmaydi

**Sabab:** Telegram'ga commandlar ro'yxati yuborilmagan

**Yechim 1 - Kod orqali:**
```bash
cd /root/erpnext_bot
.venv/bin/python set_bot_commands.py
```

**Yechim 2 - BotFather orqali:**
1. Telegram'da `@BotFather` ga `/mybots` yozing
2. O'z botingizni tanlang
3. **Edit Bot** → **Edit Commands**
4. Quyidagini yuboring:
```
start - Botni boshlash
help - Yordam va operator raqami
```

---

## 🎯 To'liq Restart Protokoli

Agar hamma narsa ishlamasa, to'liq restart qiling:

```bash
# 1. SSH orqali serverga kiring
ssh root@SERVER_IP

# 2. Bot papkasiga o'ting
cd /root/erpnext_bot

# 3. Barcha bot processlarni to'xtating
pkill -9 -f start_polling_bot
pkill -9 -f "python.*erpnext"
pkill -9 -f "uvicorn.*erpnext"

# 4. Hamma cache'ni tozalang
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null

# 5. Yangi kodni torting
git fetch origin main
git reset --hard origin/main

# 6. Deploy improved script bilan ishga tushiring
./deploy_improved.sh

# 7. Loglarni kuzating
tail -f bot_polling.log
```

---

## 📊 Diagnostic Checklist

Har safar "o'zgarishlar tushmayapti" deb o'ylasangiz, quyidagilarni tekshiring:

- [ ] `./debug_bot.sh` ni ishga tushirdingizmi?
- [ ] Kod versiyasi to'g'rimi? (`git log -1`)
- [ ] Bot process ishlayaptimi? (`ps aux | grep start_polling`)
- [ ] Python cache tozami? (*.pyc fayllar yo'q)
- [ ] Process yangi koddan keyinmi boshlangan?
- [ ] Logda xatolik bormi? (`tail -50 bot_polling.log`)
- [ ] .env fayl to'g'rimi?
- [ ] Bot token ishlayaptimi?

---

## 🚨 Tez-tez uchraydigan xatolar

### 1. "Deploy bo'ldi, lekin o'zgarish yo'q"
→ Python cache muammosi. `deploy_improved.sh` ishlatish kerak.

### 2. "CI/CD success, lekin bot eski"
→ Bot process restart bo'lmagan. Qo'lda `./deploy_improved.sh` ishga tushiring.

### 3. "Commandlar menyuda yo'q"
→ BotFather orqali commandlarni qo'lda sozlang.

### 4. "Bot ishlamayapti"
→ Loglarni tekshiring: `tail -50 bot_polling.log`

---

## 📞 Oxirgi chora

Agar hamma narsa ishlamasa:

```bash
# Bot papkasini to'liq o'chirish va qayta clone qilish
cd /root
rm -rf erpnext_bot
git clone https://github.com/ruxshona2103/erpnext_bot.git
cd erpnext_bot

# .env faylni ko'chirish (agar backup bor bo'lsa)
# yoki yangi .env yaratish

# Deploy
./deploy_improved.sh
```

---

**Yaratilgan:** 2025-12-02
**Muallif:** Claude Code + ruxshona2103
