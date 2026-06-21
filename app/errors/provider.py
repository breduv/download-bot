from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class ProviderError(Exception):
    message: str
    provider: str
    operation: str
    details: str = field(default_factory=str)

    public_message: str = field(init=False)

    code: ClassVar[str] = "provider_error"

    def __post_init__(self) -> None:
        self.public_message = self._build_public_message()
        super().__init__(self.message)

    def _build_public_message(self) -> str:
        match (self.code, self.provider, self.operation, self.details):
            # Spotify
            case ("provider_timeout", "spotify", "get_track", _):
                return "Spotify не ответил вовремя. Попробуй получить трек позже"

            case ("provider_timeout", "spotify", "search_tracks", _):
                return "Spotify не ответил вовремя. Попробуй повторить поиск позже"

            case ("track_fetch_error", "spotify", "get_track", _):
                return "Не смог получить трек из Spotify. Проверь ссылку или попробуй позже"

            case ("empty_response", "spotify", "get_track", _):
                return "Spotify вернул пустой ответ для этого трека. Попробуй позже"

            case ("track_fetch_error", "spotify", "search_tracks", _):
                return "Не смог выполнить поиск в Spotify. Попробуй позже"

            case ("empty_response", "spotify", "search_tracks", "response"):
                return "Spotify вернул пустой ответ. Попробуй позже"

            case ("empty_response", "spotify", "search_tracks", "tracks"):
                return "В Spotify ничего не найдено по этому запросу"

            # yt-dlp: аудио
            case ("download_error", "yt-dlp", "download_audio", _):
                return "Не удалось скачать аудио. Попробуй другую ссылку или запрос"

            case ("empty_response", "yt-dlp", "download_audio", "entries"):
                return "По этому запросу не удалось найти аудио"

            case ("empty_response", "yt-dlp", "download_audio", _):
                return "Не удалось получить информацию об аудио. Проверь ссылку или запрос"

            case ("unexpected_response", "yt-dlp", "download_audio", _):
                return "Не удалось обработать данные аудио. Попробуй другую ссылку или запрос"

            case ("media_too_large", "yt-dlp", "download_audio", _):
                return "Аудиофайл слишком большой для отправки. Попробуй другой трек"

            # yt-dlp: видео
            case ("download_error", "yt-dlp", "download_video", _):
                return "Не удалось скачать видео. Проверь ссылку или попробуй позже"

            case ("empty_response", "yt-dlp", "download_video", _):
                return "Не удалось получить информацию о видео. Проверь ссылку"

            case ("unexpected_response", "yt-dlp", "download_video", _):
                return "Не удалось обработать данные видео. Попробуй другую ссылку"

            case ("media_too_large", "yt-dlp", "download_video", "selected_format"):
                return "Видеофайл слишком большой для отправки. Выбери более низкое качество"

            case ("media_too_large", "yt-dlp", "download_video", _):
                return "Видеофайл слишком большой для отправки. Попробуй другую ссылку"

            # yt-dlp: получение доступных форматов видео
            case ("download_error", "yt-dlp", "get_video_formats", _):
                return "Не удалось получить форматы видео. Проверь ссылку или попробуй позже"

            case ("empty_response", "yt-dlp", "get_video_formats", "formats"):
                return "У этого видео не нашлось доступных форматов"

            case ("empty_response", "yt-dlp", "get_video_formats", _):
                return "Не удалось получить информацию о видео. Проверь ссылку"

            case ("unexpected_response", "yt-dlp", "get_video_formats", _):
                return "Не удалось разобрать доступные форматы видео"

            # Обложки и метаданные
            case ("provider_timeout", "cover", "download_cover", _):
                return "Сервис обложек не ответил вовремя. Попробуй позже"

            case ("download_error", "cover", "download_cover", _):
                return "Не удалось скачать обложку трека. Попробуй позже"

            case ("download_error", "cover", "set_mp3_cover", _):
                return "Не удалось добавить обложку к аудиофайлу"

            case ("unexpected_response", "cover", "set_mp3_cover", _):
                return "Формат обложки не поддерживается"

            case ("download_error", "cover", "set_mp3_metadata", _):
                return "Не удалось добавить данные о треке в аудиофайл"

            # fallback
            case _:
                return "Не удалось обработать медиафайл. Попробуй другую ссылку или запрос"


class TrackFetchError(ProviderError):
    code: ClassVar[str] = "track_fetch_error"


class ProviderTimeoutError(ProviderError):
    code: ClassVar[str] = "provider_timeout"


class DownloadError(ProviderError):
    code: ClassVar[str] = "download_error"


class EmptyResponseError(ProviderError):
    code: ClassVar[str] = "empty_response"


class UnexpectedResponseError(ProviderError):
    code: ClassVar[str] = "unexpected_response"


class MediaTooLargeError(ProviderError):
    code: ClassVar[str] = "media_too_large"
