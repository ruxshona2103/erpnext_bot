#!/usr/bin/env python3
"""
Bot commandlarni sozlash scripti.

Bu scriptni ishga tushirib, bot commandlarni Telegram'ga ro'yxatdan o'tkazishingiz mumkin.

Ishlatish:
    python set_bot_commands.py
"""

import asyncio
import sys
from pathlib import Path

# Loyiha papkasini yo'lga qo'shish
sys.path.insert(0, str(Path(__file__).parent))

from aiogram import Bot
from aiogram.types import BotCommand
from app.config import config


async def set_commands():
    """Bot commandlarni sozlash"""

    bot = Bot(token=config.telegram.bot_token)

    # Commandlar ro'yxati
    commands = [
        BotCommand(command="start", description="Botni boshlash"),
        BotCommand(command="help", description="Yordam va operator raqami"),
    ]

    try:
        await bot.set_my_commands(commands)
        print("✅ Bot commandlar muvaffaqiyatli sozlandi!")
        print("\nQo'shilgan commandlar:")
        for cmd in commands:
            print(f"  /{cmd.command} - {cmd.description}")
        print("\nEndi Telegram'da botingizni oching va '/' tugmasini bosing!")

    except Exception as e:
        print(f"❌ Xatolik: {e}")
        return 1

    finally:
        await bot.session.close()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(set_commands())
    sys.exit(exit_code)
