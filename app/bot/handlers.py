from pathlib import Path
from tempfile import TemporaryDirectory

from aiogram.types import Message

from app.bot.keyboard import build_search_results_keyboard
from app.services.download_service import DownloadService
from app.services.search_service import SearchService


class BotHandlers:
    def __init__(self, search_service: SearchService, download_service: DownloadService) -> None:
        self.search_service = search_service
        self.download_service = download_service

    async def handle_text(self, msg: Message) -> None:
        if not msg.text or not msg.from_user:
            return

        response = await self.search_service.search(msg.text)

        audio = response.get("audio")
        video = response.get("video")

        if audio is not None:
            with TemporaryDirectory() as temp_dir:
                file_path = await self.download_service.download_media(
                    {"audio": audio},
                    Path(temp_dir),
                )
                ...

        elif video is not None:
            with TemporaryDirectory() as temp_dir:
                file_path = await self.download_service.download_media(
                    {"video": video},
                    Path(temp_dir),
                )
                ...
        else:
            keyboard = build_search_results_keyboard(response)
            text = "Выбери вариант:"
            
            if any(key.startswith("sp:") for key in response):
                text = "Выберите трек:"

            if any(key.startswith("yt:") for key in response):
                text = "Выбери формат:"

            await msg.answer(
                text,
                reply_markup=keyboard,
            )

            