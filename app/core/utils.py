from contextlib import asynccontextmanager
from difflib import SequenceMatcher
import re
import shutil
import tempfile
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def is_url(text: str) -> bool:
    return bool(re.match(r'https?://\S+', text.strip()))

def is_spotify_url(text: str) -> bool:
    pattern = r'https?://open\.spotify\.com/(track|album|artist|playlist|episode|show)/[a-zA-Z0-9]+'
    return bool(re.match(pattern, text.strip()))

def extract_spotify_track_id(url: str) -> str | None:
    match = re.match(r'https?://open\.spotify\.com/track/([a-zA-Z0-9]+)', url.strip())
    return match.group(1) if match else None


@asynccontextmanager
async def async_tempdir():
    tmpdir = tempfile.mkdtemp()
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def create_inline_keyboard(buttons: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    """
    Создаёт инлайн-клавиатуру.
    
    :param buttons: Список строк кнопок, где каждая кнопка — кортеж (текст, callback_data).
                    Пример: [[("Кнопка 1", "callback_1")], [("Кнопка 2", "callback_2"), ("Кнопка 3", "callback_3")]]
    :return: InlineKeyboardMarkup
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=data) for text, data in row]
        for row in buttons
    ])
    return keyboard