from contextlib import asynccontextmanager
from difflib import SequenceMatcher
import re
import shutil
import tempfile
from urllib.parse import urlparse
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


YOUTUBE_VIDEO_RE = re.compile(
    r"^(https?://)?(www\.)?"
    r"(youtube\.com/(watch\?v=|shorts/|live/|embed/)|youtu\.be/)"
    r"([A-Za-z0-9_-]{6,})"
    r"([&?].*)?$"
)


def is_url(text: str) -> bool:
    return bool(re.match(r'https?://\S+', text.strip()))

def is_spotify_url(text: str) -> bool:
    pattern = r'https?://open\.spotify\.com/(track|album|artist|playlist|episode|show)/[a-zA-Z0-9]+'
    return bool(re.match(pattern, text.strip()))

def is_youtube_video_url(url: str) -> bool:
    return bool(YOUTUBE_VIDEO_RE.match(url.strip()))

def is_tiktok_video_url(url: str) -> bool:
    try:
        parsed = urlparse(url.strip())
        host = parsed.netloc.lower()
        path = parsed.path

        if host in {"vm.tiktok.com", "vt.tiktok.com"}:
            return True

        if host in {"tiktok.com", "www.tiktok.com", "m.tiktok.com"}:
            return bool(re.fullmatch(r'/@[\w.-]+/video/\d+', path))

        return False
    except Exception:
        return False

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