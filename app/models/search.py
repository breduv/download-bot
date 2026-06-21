from dataclasses import dataclass
from enum import StrEnum


class InputKind(StrEnum):
    QUERY = "query"
    SPOTIFY = "spotify"
    YOUTUBE = "youtube"
    AUDIO = "audio"
    VIDEO = "video"
    UNSUPPORTED_URL = "unsupported_url"

@dataclass(frozen=True)
class ParsedInput:
    source: InputKind
    query: str


SPOTIFY_HOSTS = {
    "open.spotify.com",
    "spotify.link",
}

PINTEREST_HOSTS = {
    "pinterest.com",
    "www.pinterest.com",
    "pinterest.ru",
    "www.pinterest.ru",
    "ru.pinterest.com",
    "pin.it",
}

YOUTUBE_MUSIC_HOSTS = {
    "music.youtube.com",
}

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
}

TIKTOK_HOSTS = {
    "tiktok.com",
    "www.tiktok.com",
    "m.tiktok.com",
    "vm.tiktok.com",
    "vt.tiktok.com",
}
