from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class TrackInfo:
    title: str
    artist: str
    cover_url: str | None
    duration_seconds: int

@dataclass(frozen=True)
class MediaFormat:
    format_id: str
    extension: str
    height: int | None
    fps: float | None
    filesize: int | None

@dataclass(frozen=True)
class DownloadedMedia:
    path: Path
    title: str | None
    duration_seconds: int | None
    filesize: int

@dataclass(frozen=True)
class DownloadedImage:
    path: Path
    mime_type: Literal["image/jpeg", "image/png", "image/webp"]