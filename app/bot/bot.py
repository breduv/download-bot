import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.session.aiohttp import AiohttpSession

from app.bot.router import router
from app.core.config import settings
from app.core.logger import get_logger


logger = get_logger(__name__)


# Всплывающий список команд бота
async def set_commands(bot: Bot):
    commands = [
        types.BotCommand(command="start", description="Знакомство с ботом")
    ]
    await bot.set_my_commands(commands)

async def start_telegram_bot():
    try:
        session = AiohttpSession(proxy=settings.PROXY2)
        bot = Bot(token=settings.BOT_TOKEN, session=session)
        dp = Dispatcher()

        # dp.message.middleware(OnlyGroupMiddleware())
        dp.include_routers(router)
        await set_commands(bot)

        logger.info("Starting Telegram bot")

        await dp.start_polling(bot)

    except Exception as e:
        logger.error(e)