from typing import ClassVar


class AppError(Exception):
    code: ClassVar[str] = "app_error"
    public_message: str = "Не удалось обработать запрос. Попробуй позже"

    def __init__(
        self,
        message: str,
        *,
        component: str,
        operation_name: str,
        details: str = "",
        public_message: str | None = None,
    ) -> None:
        super().__init__(message)

        self.message = message
        self.component = component
        self.operation_name = operation_name
        self.details = details

        if public_message is not None:
            self.public_message = public_message


class TrackFetchError(AppError):
    code: ClassVar[str] = "track_fetch_error"
    public_message: str = "Не смог получить трек. Попробуй позже"


class ProviderTimeoutError(AppError):
    code: ClassVar[str] = "provider_timeout"
    public_message: str = "Сервис не ответил вовремя. Попробуй позже"


class DownloadError(AppError):
    code: ClassVar[str] = "download_error"
    public_message: str = "Не удалось скачать файл. Попробуй позже"


class EmptyResponseError(AppError):
    code: ClassVar[str] = "empty_response"
    public_message: str = "Не удалось получить данные. Попробуй позже"


class UnexpectedResponseError(AppError):
    code: ClassVar[str] = "unexpected_response"
    public_message: str = "Не удалось обработать полученные данные. Попробуй позже"


class MediaTooLargeError(AppError):
    code: ClassVar[str] = "media_too_large"
    public_message: str = "Файл слишком большой для отправки"


class EmptyQueryError(AppError):
    code: ClassVar[str] = "empty_query"
    public_message: str = "Отправь название трека или ссылку"


class UnsupportedUrlError(AppError):
    code: ClassVar[str] = "unsupported_url"
    public_message: str = "Эта ссылка пока не поддерживается"


class UrlResolutionError(AppError):
    code: ClassVar[str] = "url_resolution_error"
    public_message: str = (
        "Не удалось раскрыть короткую ссылку TikTok. Пришли полную ссылку на публикацию"
    )


class InvalidInputKindError(AppError):
    code: ClassVar[str] = "invalid_input_kind"
    public_message: str = "Не удалось понять, что делать с этим запросом"


class InvalidCallbackDataError(AppError):
    code: ClassVar[str] = "invalid_callback_data"
    public_message: str = "Неизвестная кнопка"
