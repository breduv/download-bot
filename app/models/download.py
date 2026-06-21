from typing import NotRequired, TypedDict


class AudioDownloadPayload(TypedDict):
    audio: str
    cover_url: NotRequired[str | None]


class VideoDownloadPayload(TypedDict):
    video: str


MediaDownloadPayload = AudioDownloadPayload | VideoDownloadPayload