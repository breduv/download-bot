from aiogram import F, Router
from aiogram.filters import Command

from app.bot.handlers import BotHandlers
from app.services.download_service import DownloadService
from app.services.search_service import SearchService


def setup_router(
    search_service: SearchService,
    download_service: DownloadService,
    inline_cache_chat_id: int | None = None,
) -> Router:
    router = Router(name="main")

    handlers = BotHandlers(
        search_service=search_service,
        download_service=download_service,
        inline_cache_chat_id=inline_cache_chat_id,
    )

    router.message.register(
        handlers.handle_start,
        Command("start"),
    )

    router.message.register(
        handlers.handle_help,
        Command("help"),
    )

    router.message.register(
        handlers.handle_text,
        F.text,
        ~Command("start", "help"),
    )

    router.callback_query.register(
        handlers.handle_callback,
        F.data.startswith("sp:")
        | F.data.startswith("yt:")
        | (F.data == "inline:pending"),
    )

    router.inline_query.register(handlers.handle_inline_query)
    router.chosen_inline_result.register(handlers.handle_chosen_inline_result)

    return router
