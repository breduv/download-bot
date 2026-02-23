import asyncio
from aiogram import Bot, Dispatcher
from app.bot.router import router
from app.core.config import settings
from app.core.logger import get_logger


logger = get_logger(__name__)


# # Всплывающий список команд бота
# async def set_commands(bot: Bot):
#     commands = [
#         types.BotCommand(command="talk", description="/talk <текст> | Нейро АбAIв ответит")
#     ]
#     await bot.set_my_commands(commands)


async def keep_alive(bot: Bot):
    while True:
        try:
            await bot.get_me()
            logger.debug("[keep_alive] Telegram жив")
        except Exception as e:
            logger.error(f"[keep_alive] Ошибка: {e}")
        await asyncio.sleep(300)  # каждые 5 минут

async def start_telegram_bot():
    try:
        bot = Bot(token=settings.BOT_TOKEN)
        dp = Dispatcher()

        # dp.message.middleware(OnlyGroupMiddleware())
        dp.include_routers(router)

        logger.info("Starting Telegram bot")

        await dp.start_polling(bot)

    except Exception as e:
        logger.error(e)