from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_search_results_keyboard(results: dict[str, str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for payload, text in results.items():
        builder.button(
            text=text,
            callback_data=payload,
        )

    builder.adjust(1)

    return builder.as_markup()