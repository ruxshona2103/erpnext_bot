# ERPNext Telegram Bot

Telegram bot for ERPNext - Polling Mode (Simple & Reliable)

## Features

- Customer profile management
- Contract details with products
- Payment history with running balance
- Payment schedule tracking
- Automatic notifications for due payments
- Contract completion status display

## Deployment

### Quick Start (Polling Mode)

```bash
./deploy_polling.sh
```

This will:
- Set up Python environment
- Install dependencies
- Start bot in polling mode
- No DNS/SSL/Nginx needed!

### Configuration

Edit `.env`:
```bash
BOT_TOKEN=your_telegram_bot_token
ERP_BASE_URL=https://your-erpnext.com
ERP_API_KEY=your_api_key
ERP_API_SECRET=your_api_secret
```

### Management

- View logs: `tail -f bot_polling.log`
- Check status: `./check_status.sh`
- Restart: `./deploy_polling.sh`

## Requirements

- Python 3.10+
- ERPNext v14+
- Telegram Bot Token

See `requirements.txt` for Python dependencies.
