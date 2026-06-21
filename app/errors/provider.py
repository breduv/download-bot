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
            # Spotify: получение трека по ссылке / id
            case ("track_fetch_error", "spotify", "get_track", _):
                return "Не смог получить трек из Spotify. Проверь ссылку или попробуй позже"

            case ("empty_response", "spotify", "get_track", _):
                return "Spotify не вернул трек по этой ссылке или ID"

            # Spotify: поиск треков
            case ("track_fetch_error", "spotify", "search_tracks", _):
                return "Не смог выполнить поиск в Spotify. Попробуй позже"

            case ("empty_response", "spotify", "search_tracks", _):
                return "Spotify ничего не вернул по этому запросу"

            # yt-dlp: скачивание / извлечение
            case ("download_error", "yt-dlp", "download", _):
                return "Не удалось скачать медиафайл. Проверь ссылку или попробуй позже"

            case ("empty_response", "yt-dlp", "download", "extract_info"):
                return "Не удалось получить информацию о видео. Попробуй другую ссылку"

            case ("empty_response", "yt-dlp", "download", "entries"):
                return "По этому запросу не нашлось подходящего видео"

            case ("unexpected_response", "yt-dlp", "download", "info_type"):
                return "Сервис вернул неожиданный ответ. Попробуй другую ссылку"

            case ("unexpected_response", "yt-dlp", "download", "entries_type"):
                return "Не удалось разобрать результаты поиска видео"

            case ("unexpected_response", "yt-dlp", "download", "entry_type"):
                return "Не удалось разобрать найденное видео"

            # yt-dlp: получение доступных форматов видео
            case ("download_error", "yt-dlp", "get_video_formats", _):
                return "Не удалось получить форматы видео. Проверь ссылку или попробуй позже"

            case ("empty_response", "yt-dlp", "get_video_formats", "formats"):
                return "У этого видео не нашлось доступных форматов"

            case ("empty_response", "yt-dlp", "get_video_formats", _):
                return "Не удалось получить информацию о видео. Проверь ссылку"

            case ("unexpected_response", "yt-dlp", "get_video_formats", _):
                return "Не удалось разобрать доступные форматы видео"

            # yt-dlp: проверка скачанного файла
            case ("media_too_large", "yt-dlp", "download_media", _):
                return "Файл слишком большой для отправки. Попробуй другую ссылку или более низкое качество"

            case ("download_error", "yt-dlp", "download_media", "file_missing"):
                return "Скачивание завершилось без файла. Попробуй ещё раз позже"

            case ("unexpected_response", "yt-dlp", "download_media", "missing_media_id"):
                return "Не удалось определить скачанный файл. Попробуй другую ссылку"

            # Обложки и метаданные
            case ("download_error", "cover", "download_cover", _):
                return "Не удалось скачать обложку трека. Попробуй позже"

            case ("download_error", "cover", "set_mp3_cover", _):
                return "Не удалось добавить обложку к аудиофайлу"

            case ("unexpected_response", "cover", "set_mp3_cover", "unsupported_cover_extension"):
                return "Формат обложки не поддерживается"

            case ("download_error", "cover", "set_mp3_metadata", _):
                return "Не удалось добавить данные о треке в аудиофайл"

            # fallback
            case _:
                return "Не удалось обработать трек. Попробуй другую ссылку или запрос."


class TrackFetchError(ProviderError):
    code: ClassVar[str] = "track_fetch_error"


class DownloadError(ProviderError):
    code: ClassVar[str] = "download_error"


class EmptyResponseError(ProviderError):
    code: ClassVar[str] = "empty_response"


class UnexpectedResponseError(ProviderError):
    code: ClassVar[str] = "unexpected_response"


class MediaTooLargeError(ProviderError):
    code: ClassVar[str] = "media_too_large"