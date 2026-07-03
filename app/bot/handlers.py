from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
from uuid import uuid4

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultCachedAudio,
    InlineQueryResultCachedPhoto,
    InlineQueryResultCachedVideo,
    InlineQueryResultUnion,
    InlineQueryResultsButton,
    InputMediaPhoto,
    InputTextMessageContent,
    Message,
)

from app.bot.keyboard import build_search_results_keyboard
from app.errors.base import (
    AppError,
    InvalidCallbackDataError,
    UnexpectedResponseError,
)
from app.services.download_service import DownloadService
from app.services.search_service import SearchService


logger = getLogger(__name__)


class BotHandlers:
    def __init__(
        self,
        search_service: SearchService,
        download_service: DownloadService,
        inline_cache_chat_id: int | None = None,
    ) -> None:
        self.search_service = search_service
        self.download_service = download_service
        self.inline_cache_chat_id = inline_cache_chat_id

    async def handle_text(self, msg: Message) -> None:
        try:
            if msg.text is None or not msg.from_user:
                return

            logger.info(
                "Text request received user_id=%s chat_id=%s text_length=%d",
                msg.from_user.id,
                msg.chat.id,
                len(msg.text),
            )

            response = await self.search_service.search(msg.text)

            if response.get("audio") is not None:
                logger.info("Audio request resolved user_id=%s", msg.from_user.id)
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
                        logger.info("Audio sent user_id=%s", msg.from_user.id)
                finally:
                    await self._delete_message(loading_msg)

                return

            if response.get("video") is not None:
                logger.info("Video request resolved user_id=%s", msg.from_user.id)
                loading_msg = await msg.answer("Скачиваю...")
                try:
                    with TemporaryDirectory() as temp_dir:
                        file_path, _ = await self.download_service.download_media(
                            response,
                            Path(temp_dir),
                        )

                        await msg.answer_video(video=FSInputFile(file_path), supports_streaming=True)
                        logger.info("Video sent user_id=%s", msg.from_user.id)
                finally:
                    await self._delete_message(loading_msg)

                return
            
            if response.get("photo") is not None:
                logger.info("Photo request resolved user_id=%s", msg.from_user.id)
                loading_msg = await msg.answer("Скачиваю...")
                try:
                    with TemporaryDirectory() as temp_dir:
                        photo_paths = await self.download_service.download_photos(
                            response["photo"],
                            Path(temp_dir),
                        )

                        await self._send_photos(msg, photo_paths)
                        logger.info(
                            "Gallery sent user_id=%s photos_count=%d",
                            msg.from_user.id,
                            len(photo_paths),
                        )
                finally:
                    await self._delete_message(loading_msg)

                return

            keyboard = build_search_results_keyboard(response)
            text = "Выбери вариант:"

            if any(key.startswith("sp:") for key in response):
                text = "Выбери трек:"
            elif any(key.startswith("yt:") for key in response):
                text = "Выбери формат:"

            await msg.answer(text, reply_markup=keyboard)
            logger.info(
                "Selection keyboard sent user_id=%s options_count=%d",
                msg.from_user.id,
                len(response),
            )

            return
        except AppError as exc:
            self._log_handled_error("text", exc)
            await self._send_error(msg, exc.public_message)
        except Exception:
            logger.exception("Unhandled request error context=text")
            await self._send_error(msg, "Произошла непредвиденная ошибка. Попробуй ещё раз позже")

    async def handle_callback(self, callback: CallbackQuery) -> None:
        try:
            if callback.data is None:
                return 

            if not isinstance(callback.message, Message):
                raise InvalidCallbackDataError(
                    "Callback message is missing",
                    component="bot",
                    operation_name="handle_callback",
                    public_message="Не удалось найти сообщение",
                )

            msg = callback.message
            data = callback.data

            logger.info(
                "Callback received user_id=%s chat_id=%s callback_type=%s",
                callback.from_user.id,
                msg.chat.id,
                data.partition(":")[0],
            )

            await callback.answer()

            if data.startswith("sp:"):
                track_id = data.removeprefix("sp:")
                if not track_id:
                    raise InvalidCallbackDataError(
                        "Spotify callback track id is empty",
                        component="bot",
                        operation_name="handle_callback",
                    )

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
                        logger.info("Spotify audio sent user_id=%s", callback.from_user.id)
                finally:
                    await self._delete_message(loading_msg)

                return

            if data.startswith("yt:"):
                parts = data.split(":", maxsplit=2)
                if len(parts) != 3 or not parts[1] or not parts[2]:
                    raise InvalidCallbackDataError(
                        f"Malformed YouTube callback data: {data}",
                        component="bot",
                        operation_name="handle_callback",
                    )

                _, video_id, format_id = parts
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
                            logger.info("YouTube audio sent user_id=%s", callback.from_user.id)
                        else:
                            await msg.answer_video(video=FSInputFile(file_path), supports_streaming=True)
                            logger.info(
                                "YouTube video sent user_id=%s format_id=%s",
                                callback.from_user.id,
                                format_id,
                            )
                finally:
                    await self._delete_message(loading_msg)

                return

            raise InvalidCallbackDataError(
                f"Unknown callback data: {data}",
                component="bot",
                operation_name="handle_callback",
            )
        except AppError as exc:
            self._log_handled_error("callback", exc)
            await self._send_callback_error(callback, exc.public_message)
        except Exception:
            logger.exception("Unhandled request error context=callback")
            await self._send_callback_error(
                callback,
                "Произошла непредвиденная ошибка. Попробуй отправить запрос ещё раз.",
            )

    async def handle_inline_query(self, inline_query: InlineQuery, bot: Bot) -> None:
        query = inline_query.query.strip()

        if not query or not (urlparse(query).scheme in ("http", "https") and urlparse(query).hostname is not None):
            await bot.answer_inline_query(inline_query_id=inline_query.id, results=[], cache_time=1)
            return

        try:
            logger.info(
                "Inline request received user_id=%s query_length=%d",
                inline_query.from_user.id,
                len(query),
            )

            response = await self.search_service.search(query)

            with TemporaryDirectory() as temp_dir:
                results = await self._build_inline_results(
                    bot,
                    inline_query,
                    response,
                    Path(temp_dir),
                )

            await bot.answer_inline_query(
                inline_query_id=inline_query.id,
                results=results,
            )
            
            logger.info(
                "Inline request answered user_id=%s results_count=%d",
                inline_query.from_user.id,
                len(results),
            )
        except TelegramForbiddenError:
            logger.warning(
                "Inline upload target is unavailable user_id=%s cache_chat_id=%s",
                inline_query.from_user.id,
                self.inline_cache_chat_id,
                exc_info=True,
            )
            if self.inline_cache_chat_id is None:
                public_message = "Сначала открой бота в личке, потом повтори inline-запрос"
                result = InlineQueryResultArticle(
                    id=uuid4().hex,
                    title=public_message,
                    description="Попробуй другую ссылку",
                    input_message_content=InputTextMessageContent(message_text=public_message),
                )

                try:
                    await bot.answer_inline_query(
                        inline_query_id=inline_query.id,
                        results=[result],
                        cache_time=1,
                        is_personal=True,
                        button=InlineQueryResultsButton(
                            text="Открыть бота",
                            start_parameter="inline",
                        ),
                    )
                except TelegramAPIError:
                    logger.warning("Failed to answer inline query with start hint", exc_info=True)

                return

            await self._answer_inline_error(
                bot,
                inline_query,
                "Бот не может загрузить файл в служебный чат",
            )
        except AppError as exc:
            self._log_handled_error("inline_query", exc)
            await self._answer_inline_error(bot, inline_query, exc.public_message)
        except TelegramAPIError:
            logger.exception("Telegram API error context=inline_query")
            await self._answer_inline_error(
                bot,
                inline_query,
                "Telegram не принял файл. Попробуй другую ссылку",
            )
        except Exception:
            logger.exception("Unhandled request error context=inline_query")
            await self._answer_inline_error(
                bot,
                inline_query,
                "Произошла непредвиденная ошибка. Попробуй ещё раз позже",
            )

    async def _build_inline_results(
        self,
        bot: Bot,
        inline_query: InlineQuery,
        response: dict[str, str],
        temp_dir: Path,
    ) -> list[InlineQueryResultUnion]:
        if response.get("audio") is not None:
            file_path, cover_path = await self.download_service.download_media(response, temp_dir)

            upload_msg = await bot.send_audio(
                chat_id=self.inline_cache_chat_id or inline_query.from_user.id,
                audio=FSInputFile(file_path),
                thumbnail=FSInputFile(cover_path) if cover_path is not None else None,
                title=response.get("title"),
                performer=response.get("artist"),
                disable_notification=True,
            )
            
            try:
                if upload_msg.audio is None:
                    raise UnexpectedResponseError(
                        "Telegram did not return uploaded audio",
                        component="telegram",
                        operation_name="upload_inline_audio",
                        public_message="Не удалось подготовить аудио для inline-отправки",
                    )

                return [InlineQueryResultCachedAudio(
                    id=uuid4().hex,
                    audio_file_id=upload_msg.audio.file_id,
                )]
            finally:
                await self._delete_message(upload_msg)

        if response.get("video") is not None:
            file_path, _ = await self.download_service.download_media(response, temp_dir)

            upload_msg = await bot.send_video(
                chat_id=self.inline_cache_chat_id or inline_query.from_user.id,
                video=FSInputFile(file_path),
                supports_streaming=True,
                disable_notification=True,
            )
            try:
                if upload_msg.video is None:
                    raise UnexpectedResponseError(
                        "Telegram did not return uploaded video",
                        component="telegram",
                        operation_name="upload_inline_video",
                        public_message="Не удалось подготовить видео для inline-отправки",
                    )

                return [InlineQueryResultCachedVideo(
                    id=uuid4().hex,
                    video_file_id=upload_msg.video.file_id,
                    title="Видео",
                )]
            finally:
                await self._delete_message(upload_msg)

        if response.get("photo") is not None:
            photo_paths = await self.download_service.download_photos(
                response["photo"],
                temp_dir,
            )

            results: list[InlineQueryResultUnion] = []
            max_results = 10
            total = min(len(photo_paths), max_results)

            for index, photo_path in enumerate(photo_paths[:max_results], start=1):
                upload_msg = await bot.send_photo(
                    chat_id=self.inline_cache_chat_id or inline_query.from_user.id,
                    photo=FSInputFile(photo_path),
                    disable_notification=True,
                )
                try:
                    if not upload_msg.photo:
                        raise UnexpectedResponseError(
                            "Telegram did not return uploaded photo",
                            component="telegram",
                            operation_name="upload_inline_photo",
                            public_message="Не удалось подготовить фото для inline-отправки",
                        )

                    results.append(
                        InlineQueryResultCachedPhoto(
                            id=uuid4().hex,
                            photo_file_id=upload_msg.photo[-1].file_id,
                            title=f"Фото {index}/{total}",
                        )
                    )
                finally:
                    await self._delete_message(upload_msg)

            return results

        raise InvalidCallbackDataError(
            "Inline query resolved to unsupported selection results",
            component="bot",
            operation_name="handle_inline_query",
            public_message="Inline-режим сейчас работает только со ссылками",
        )

    @staticmethod
    async def _send_photos(msg: Message, photo_paths: list[Path]) -> None:
        max_group_size = 10

        for start in range(0, len(photo_paths), max_group_size):
            batch = photo_paths[start:start + max_group_size]
            logger.debug("Sending photo batch photos_count=%d", len(batch))

            if len(batch) == 1:
                await msg.answer_photo(photo=FSInputFile(batch[0]))
                continue

            media = [
                InputMediaPhoto(media=FSInputFile(photo_path))
                for photo_path in batch
            ]
            await msg.answer_media_group(media=media) # pyright: ignore[reportArgumentType]

    @staticmethod
    def _log_handled_error(
        context: str,
        exc: AppError,
    ) -> None:
        logger.warning(
            "Handled request error context=%s code=%s component=%s operation_name=%s details=%s",
            context,
            exc.code,
            exc.component,
            exc.operation_name,
            exc.details,
            # exc_info=True,
        )

    @staticmethod
    async def _delete_message(msg: Message) -> None:
        try:
            await msg.delete()
        except Exception:
            logger.warning("Failed to delete message", exc_info=True)

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

    async def _answer_inline_error(
        self,
        bot: Bot,
        inline_query: InlineQuery,
        public_message: str,
    ) -> None:
        result = InlineQueryResultArticle(
            id=uuid4().hex,
            title=public_message,
            description="Попробуй другую ссылку",
            input_message_content=InputTextMessageContent(message_text=public_message),
        )

        try:
            await bot.answer_inline_query(inline_query_id=inline_query.id, results=[result], cache_time=1)
        except TelegramAPIError:
            logger.warning("Failed to answer inline query with error", exc_info=True)
