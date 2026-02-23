import asyncio
from app.bot.bot import start_telegram_bot
from app.core.logger import get_logger

get_logger('aiogram')

if __name__ == "__main__":
    asyncio.run(start_telegram_bot())