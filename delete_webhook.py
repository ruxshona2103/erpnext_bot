#!/usr/bin/env python3
"""
Telegram Bot webhook'ini o'chirish uchun script.
Token .env faylidan olinadi.
"""
import os
import requests
from dotenv import load_dotenv

def main():
    # .env faylini yuklash
    load_dotenv()
    token = os.getenv('BOT_TOKEN')

    if not token:
        print("❌ BOT_TOKEN topilmadi .env faylida!")
        print("📝 .env faylini tekshiring.")
        exit(1)

    print("🔄 Webhook o'chirilmoqda...")

    try:
        # Webhook'ni o'chirish
        url = f"https://api.telegram.org/bot{token}/deleteWebhook"
        response = requests.post(url, json={'drop_pending_updates': True}, timeout=10)
        result = response.json()

        print("\n🔧 Webhook o'chirish natijasi:")
        if result.get('ok'):
            print(f"✅ {result.get('description', 'Muvaffaqiyatli')}")
        else:
            print(f"❌ {result.get('description', 'Xato yuz berdi')}")

        # Webhook info
        print("\n📊 Hozirgi webhook holati:")
        info_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
        info_response = requests.get(info_url, timeout=10)
        info = info_response.json()

        if info.get('ok'):
            webhook_info = info.get('result', {})
            webhook_url = webhook_info.get('url', '')
            if webhook_url:
                print(f"⚠️  Webhook hali o'rnatilgan: {webhook_url}")
            else:
                print("✅ Webhook yo'q - polling mode ishlashi mumkin")
        else:
            print(f"❌ {info.get('description', 'Info olishda xato')}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Tarmoq xatosi: {e}")
        exit(1)
    except Exception as e:
        print(f"❌ Xato: {e}")
        exit(1)

if __name__ == "__main__":
    main()
