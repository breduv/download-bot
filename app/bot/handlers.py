from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory

from aiogram.types import CallbackQuery, FSInputFile, Message

from app.bot.keyboard import build_search_results_keyboard
from app.errors.provider import ProviderError
from app.errors.service import InvalidCallbackDataError, ServiceError
from app.services.download_service import DownloadService
from app.services.search_service import SearchService


logger = getLogger(__name__)


class BotHandlers:
    def __init__(self, search_service: SearchService, download_service: DownloadService) -> None:
        self.search_service = search_service
        self.download_service = download_service

    async def handle_text(self, msg: Message) -> None:
        try:
            if msg.text is None or not msg.from_user:
                return

            response = await self.search_service.search(msg.text)

            if response.get("audio") is not None:
                loading_msg = await msg.answer("Скачиваю...")
                try:
                    with TemporaryDirectory() as temp_dir:
                        file_path, cover_path = await self.download_service.download_media(
                            response,
                            Path(temp_dir),
                        )

                        await msg.answer_audio(
                            audio=FSInputFile(file_path),
                            thumbnail=FSInputFile(cover_path) if cover_path is not None else None,
                        )
                finally:
                    await self._delete_loading_message(loading_msg)

                return

            if response.get("video") is not None:
                loading_msg = await msg.answer("Скачиваю...")
                try:
                    with TemporaryDirectory() as temp_dir:
                        file_path, _ = await self.download_service.download_media(
                            response,
                            Path(temp_dir),
                        )

                        await msg.answer_video(video=FSInputFile(file_path))
                finally:
                    await self._delete_loading_message(loading_msg)

                return

            keyboard = build_search_results_keyboard(response)
            text = "Выбери вариант:"

            if any(key.startswith("sp:") for key in response):
                text = "Выбери трек:"
            elif any(key.startswith("yt:") for key in response):
                text = "Выбери формат:"

            await msg.answer(text, reply_markup=keyboard)

            return
        except (ProviderError, ServiceError) as exc:
            logger.warning("Failed to handle text message: %s", exc, exc_info=True)
            await self._send_error(msg, exc.public_message)
        except Exception:
            logger.exception("Unexpected error while handling text message")
            await self._send_error(msg, "Произошла непредвиденная ошибка. Попробуй ещё раз позже")

    async def handle_callback(self, callback: CallbackQuery) -> None:
        try:
            if callback.data is None:
                await callback.answer("Пустая кнопка", show_alert=True)
                return

            if not isinstance(callback.message, Message):
                await callback.answer("Не удалось найти сообщение", show_alert=True)
                return

            msg = callback.message
            data = callback.data

            await callback.answer()

            if data.startswith("sp:"):
                track_id = data.removeprefix("sp:")

                loading_msg = await msg.answer("Скачиваю...")
                try:
                    with TemporaryDirectory() as temp_dir:
                        file_path, cover_path = await self.download_service.download_on_spotify(
                            track_id,
                            Path(temp_dir),
                        )

                        await msg.answer_audio(
                            audio=FSInputFile(file_path),
                            thumbnail=FSInputFile(cover_path) if cover_path is not None else None,
                        )
                finally:
                    await self._delete_loading_message(loading_msg)

                return

            if data.startswith("yt:"):
                _, video_id, format_id = data.split(":", maxsplit=2)
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                loading_msg = await msg.answer("Скачиваю...")
                try:
                    with TemporaryDirectory() as temp_dir:
                        file_path, cover_path = await self.download_service.download_on_youtube(
                            video_url,
                            format_id,
                            Path(temp_dir),
                        )

                        if format_id == "-1":
                            await msg.answer_audio(
                                audio=FSInputFile(file_path),
                                thumbnail=FSInputFile(cover_path) if cover_path is not None else None,
                            )
                        else:
                            await msg.answer_video(video=FSInputFile(file_path))
                finally:
                    await self._delete_loading_message(loading_msg)

                return

            raise InvalidCallbackDataError(
                f"Unknown callback data: {data}",
                service="bot",
                operation="handle_callback",
                details="unknown_prefix",
            )
        except (ProviderError, ServiceError) as exc:
            logger.warning("Failed to handle callback: %s", exc, exc_info=True)
            await self._send_callback_error(callback, exc.public_message)
        except Exception:
            logger.exception("Unexpected error while handling callback")
            await self._send_callback_error(
                callback,
                "Произошла непредвиденная ошибка. Попробуй отправить запрос ещё раз.",
            )

    @staticmethod
    async def _delete_loading_message(loading_msg: Message) -> None:
        try:
            await loading_msg.delete()
        except Exception:
            logger.warning("Failed to delete loading message", exc_info=True)

    @staticmethod
    async def _send_error(msg: Message, public_message: str) -> None:
        try:
            await msg.answer(public_message)
        except Exception:
            logger.exception("Failed to send error message to user")

    async def _send_callback_error(self, callback: CallbackQuery, public_message: str) -> None:
        if isinstance(callback.message, Message):
            await self._send_error(callback.message, public_message)
            return

        try:
            await callback.answer(public_message, show_alert=True)
        except Exception:
            logger.exception("Failed to send callback error to user")
