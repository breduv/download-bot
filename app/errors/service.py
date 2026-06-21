from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class ServiceError(Exception):
    message: str
    service: str
    operation: str = field(default_factory=str)
    details: str = field(default_factory=str)

    public_message: str = field(init=False)

    code: ClassVar[str] = "service_error"

    def __post_init__(self) -> None:
        self.public_message = self._build_public_message()
        super().__init__(self.message)

    def _build_public_message(self) -> str:
        match (self.code, self.service, self.operation, self.details):
            case ("empty_query", _, _, _):
                return "Отправь название трека или ссылку"

            case ("unsupported_url", _, _, _):
                return "Эта ссылка пока не поддерживается"

            case ("invalid_input_kind", "download", "download_media", _):
                return "Не удалось определить, что нужно скачать. Отправь запрос ещё раз"

            case ("invalid_input_kind", _, _, _):
                return "Не удалось понять, что делать с этим запросом"

            case ("invalid_callback_data", _, _, _):
                return "Неизвестная кнопка"

            case _:
                return "Не удалось обработать запрос."


class EmptyQueryError(ServiceError):
    code: ClassVar[str] = "empty_query"


class UnsupportedUrlError(ServiceError):
    code: ClassVar[str] = "unsupported_url"


class InvalidInputKindError(ServiceError):
    code: ClassVar[str] = "invalid_input_kind"


class InvalidCallbackDataError(ServiceError):
    code: ClassVar[str] = "invalid_callback_data"
