from logging import getLogger
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from app.core.config import get_settings

from app.bot.router import create_router
from app.providers.spotify import SpotifyProvider
from app.providers.ytdlp import YtdlpProvider
from app.services.download_service import DownloadService
from app.services.search_service import SearchService


logger = getLogger(__name__)
settings = get_settings()


async def run_application() -> None:
    session = AiohttpSession(proxy=settings.telegram_proxy.get_secret_value() if settings.telegram_proxy else None)
    bot = Bot(token=settings.bot_token.get_secret_value(), session=session)
    dispatcher = Dispatcher()

    storage = MemoryStateStorage(ttl_seconds=900)

    spotify = SpotifyProvider(settings)
    ytdlp = YtdlpProvider(settings)

    search_service = SearchService(
        spotify=spotify,
        ytdlp=ytdlp,
        storage=storage,
    )
    download_service = DownloadService(
        ytdlp=ytdlp,
        storage=storage,
        max_concurrent_downloads=3,
    )

    router = create_router(
        search_service=search_service,
        download_service=download_service,
    )
    dispatcher.include_router(router)

    try:
        # await bot.set_my_commands(...)
        logger.info("Starting Telegram bot")
        await dispatcher.start_polling(bot)
    finally:
        await storage.close()
        await bot.session.close()
