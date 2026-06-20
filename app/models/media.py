from pathlib import Path

from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class TrackInfo:
    title: str
    artist: str
    cover_url: str | None
    track_id: str

@dataclass(frozen=True)
class DownloadedMedia:
    filesize: int
    path: Path

@dataclass(frozen=True)
class AvailableVideoFormat:
    format_id: int
    height: int