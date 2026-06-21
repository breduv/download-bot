from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class SearchServiceError(Exception):
    message: str
    service: str
    operation: str = field(default_factory=str)
    details: str = field(default_factory=str)

    public_message: str = field(init=False)

    code: ClassVar[str] = "search_service_error"

    def __post_init__(self) -> None:
        self.public_message = self._build_public_message()
        super().__init__(self.message)

    def _build_public_message(self) -> str:
        match (self.code, self.details):
            case ("empty_query", _):
                return "Отправь название трека или ссылку."

            case ("unsupported_url", _):
                return "Эта ссылка пока не поддерживается."

            case ("invalid_input_kind", _):
                return "Не удалось понять, что делать с этим запросом."

            case _:
                return "Не удалось обработать запрос."


class EmptyQueryError(SearchServiceError):
    code: ClassVar[str] = "empty_query"


class UnsupportedUrlError(SearchServiceError):
    code: ClassVar[str] = "unsupported_url"


class InvalidInputKindError(SearchServiceError):
    code: ClassVar[str] = "invalid_input_kind"