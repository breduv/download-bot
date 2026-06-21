from aiogram import F, Router

from app.bot.handlers import BotHandlers
from app.services.download_service import DownloadService
from app.services.search_service import SearchService


def setup_router(search_service: SearchService, download_service: DownloadService) -> Router:
    router = Router(name="main")

    handlers = BotHandlers(
        search_service=search_service,
        download_service=download_service,
    )

    router.message.register(
        handlers.handle_text,
        F.text,
    )

    return router