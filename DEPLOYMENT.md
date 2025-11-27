# 🚀 Deployment Guide

## Quick Deploy

```bash
./deploy.sh
```

That's it! The script will:
1. Stop running bot
2. **Clean Python cache** (fixes stale code issues)
3. Pull latest code from Git
4. Check/update .env file
5. Test imports
6. Start bot with proper flags

---

## Manual Deploy (if script fails)

```bash
# 1. Stop bot
pkill -9 -f uvicorn

# 2. Clean cache (IMPORTANT!)
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete

# 3. Pull code
git pull origin main

# 4. Check .env
cat .env | grep SUPPORT_PHONE
# If not found, add:
echo "SUPPORT_PHONE=+998 99 123 45 67" >> .env
echo "SUPPORT_NAME=Operator" >> .env

# 5. Start bot (with no-bytecode flag)
PYTHONDONTWRITEBYTECODE=1 nohup .venv/bin/python -B -m uvicorn app.webhook.server:app --host 0.0.0.0 --port 8001 --reload > bot.log 2>&1 &
```

---

## Why Clean Cache?

Python creates `.pyc` (bytecode) files in `__pycache__/` directories. These files can become stale when you update code via git pull.

**Problem:**
- You pull new code: `support = await get_support_contact()`
- But Python uses old cache: `support = config.support.phone`
- Bot shows old behavior!

**Solution:**
- Delete `__pycache__/` and `.pyc` files before starting bot
- Use `-B` flag (don't write bytecode)
- Use `PYTHONDONTWRITEBYTECODE=1` environment variable

---

## Troubleshooting

### Bot shows old code behavior

```bash
# Clean cache and restart
find . -type d -name "__pycache__" -exec rm -rf {} +
pkill -f uvicorn
./deploy.sh
```

### Port 8001 already in use

```bash
# Find and kill process
lsof -ti:8001 | xargs kill -9
```

### Import errors

```bash
# Test imports
.venv/bin/python -c "from app.services.support import get_support_contact_sync; print('OK')"
```

---

## Logs

```bash
# View logs
tail -f bot.log

# Last 50 lines
tail -50 bot.log

# Search for errors
grep -i error bot.log
grep -i "support contact" bot.log
```

---

## Process Management

```bash
# Check if bot is running
ps aux | grep uvicorn

# Stop bot
pkill -f uvicorn

# Restart bot
./deploy.sh
```

---

## First Time Setup

1. Clone repo:
   ```bash
   git clone <repo-url>
   cd erpnext_bot
   ```

2. Create virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configure `.env`:
   ```bash
   cp .env.example .env
   nano .env  # Edit with your credentials
   ```

4. Deploy:
   ```bash
   ./deploy.sh
   ```

---

## Production Setup (systemd)

Create `/etc/systemd/system/erpnext-bot.service`:

```ini
[Unit]
Description=ERPNext Telegram Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/your-user/erpnext_bot
Environment="PYTHONDONTWRITEBYTECODE=1"
ExecStart=/home/your-user/erpnext_bot/.venv/bin/python -B -m uvicorn app.webhook.server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable erpnext-bot
sudo systemctl start erpnext-bot
sudo systemctl status erpnext-bot
```

Deploy with systemd:
```bash
# In deploy.sh, replace "nohup ..." with:
sudo systemctl restart erpnext-bot
```
