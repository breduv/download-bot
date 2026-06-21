import asyncio
from pathlib import Path
from typing import Any, cast

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError as YtdlpDownloadError

from app.core.config import Settings
from app.errors.provider import DownloadError, EmptyResponseError, MediaTooLargeError, ProviderError, UnexpectedResponseError
from app.models.media import AvailableVideoFormat


class YtdlpProvider:
    def __init__(self, settings: Settings) -> None:
        self.base_options: dict[str, Any] = {
            "quiet": True,
            "no_warnings": False,
            "noplaylist": True
        }
        if settings.media_proxy:
            self.base_options["proxy"] = settings.media_proxy.get_secret_value()
        
        self.max_upload_size_bytes = settings.max_upload_size_mb * 1024 * 1024

    def _download(self, target: str, options: dict[str, Any]) -> dict[str, Any]:
        try:
            with YoutubeDL(options) as ydl: # pyright: ignore[reportArgumentType]
                raw_info = ydl.extract_info(target, download=True)

                if raw_info is None:
                    raise EmptyResponseError(
                        "yt-dlp returned empty response",
                        provider="yt-dlp",
                        operation="download",
                        details="extract_info"
                    )
                    
                info = ydl.sanitize_info(raw_info)

        except YtdlpDownloadError as exc:
            raise DownloadError(
                "yt-dlp failed to download target",
                provider="yt-dlp",
                operation="download"
            ) from exc

        if not isinstance(info, dict):
            raise UnexpectedResponseError(
                f"yt-dlp returned unexpected response type: {type(info).__name__}",
                provider="yt-dlp",
                operation="download",
                details="info_type"
            )
        
        entries = info.get("entries")

        if entries is None:
            return cast(dict[str, Any], info)

        if not isinstance(entries, list):
            raise UnexpectedResponseError(
                "yt-dlp returned invalid entries",
                provider="yt-dlp",
                operation="download",
                details="entries_type"
            )

        if len(entries) == 0:
            raise EmptyResponseError(
                "yt-dlp returned empty entries",
                provider="yt-dlp",
                operation="download",
                details="entries"
            )

        entry = entries[0]

        if not isinstance(entry, dict):
            raise UnexpectedResponseError(
                "yt-dlp returned invalid entry",
                provider="yt-dlp",
                operation="download",
                details="entry_type"
            )

        return cast(dict[str, Any], entry)
    
    def _download_audio_sync(self, query_or_url: str, output_dir: Path) -> Path:
        options = self.base_options | {
            "format": "bestaudio/best[acodec!=none]",
            "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
            "writethumbnail": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                },
                {
                    "key": "FFmpegMetadata",
                },
                {
                    "key": "EmbedThumbnail",
                },
            ],
        }

        target = (
            query_or_url
            if query_or_url.startswith(("http://", "https://"))
            else f"ytsearch1:{query_or_url}"
        )

        info = self._download(target, options)

        media_id = info.get("id")
        if media_id is None:
            raise UnexpectedResponseError(
                "yt-dlp returned info without media id",
                provider="yt-dlp",
                operation="download_media",
                details="missing_media_id",
            )

        file_path = output_dir / (media_id+".mp3")
        if not file_path.is_file():
            raise DownloadError(
                "downloaded file was not found",
                provider="yt-dlp",
                operation="download_media",
                details="file_missing",
            )

        filesize = file_path.stat().st_size
        
        if filesize > self.max_upload_size_bytes:
            raise MediaTooLargeError(
                "downloaded media file is too large",
                provider="yt-dlp",
                operation="download_media",
                details="file_too_large",
            )
        
        return file_path
    
    async def download_audio(self, query_or_url: str, output_dir: Path) -> Path:
        return await asyncio.to_thread(
            self._download_audio_sync,
            query_or_url,
            output_dir,
        )
        
    def _download_video_sync(self, url: str, format_id: str | None, output_dir: Path) -> Path:
        if format_id == None:
            format = "bestvideo*"
        else:
            format = format_id
        options = self.base_options | {
            'format': f'{format}+bestaudio/best',
            "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
            "merge_output_format": "mp4",
            "recodevideo": "mp4",
        }

        info = self._download(url, options)

        media_id = info.get("id")
        if media_id is None:
            raise UnexpectedResponseError(
                "yt-dlp returned info without media id",
                provider="yt-dlp",
                operation="download_media",
                details="missing_media_id",
            )

        file_path = output_dir / (media_id+".mp4")
        if not file_path.is_file():
            raise DownloadError(
                "downloaded file was not found",
                provider="yt-dlp",
                operation="download_media",
                details="file_missing",
            )

        filesize = file_path.stat().st_size
        
        if filesize > self.max_upload_size_bytes:
            raise MediaTooLargeError(
                "downloaded media file is too large",
                provider="yt-dlp",
                operation="download_media",
                details="file_too_large",
            )
        
        return file_path
    
    async def download_video(self, url: str, output_dir: Path, format_id: str|None = None) -> Path:
        return await asyncio.to_thread(
            self._download_video_sync,
            url,
            format_id,
            output_dir,
        )
        
    def _get_video_formats_sync(self, url: str) -> list[AvailableVideoFormat]:
        options = self.base_options | {
            "skip_download": True,
        }

        try:
            with YoutubeDL(options) as ydl:  # pyright: ignore[reportArgumentType]
                raw_info = ydl.extract_info(url, download=False)

                if raw_info is None:
                    raise EmptyResponseError(
                        "yt-dlp returned empty response",
                        provider="yt-dlp",
                        operation="get_video_formats",
                        details="extract_info",
                    )

                info = ydl.sanitize_info(raw_info)

        except YtdlpDownloadError as exc:
            raise DownloadError(
                "yt-dlp failed to extract video formats",
                provider="yt-dlp",
                operation="get_video_formats",
            ) from exc

        if not isinstance(info, dict):
            raise UnexpectedResponseError(
                f"yt-dlp returned unexpected response type: {type(info).__name__}",
                provider="yt-dlp",
                operation="get_video_formats",
                details="info_type",
            )

        formats = info.get("formats")

        if not isinstance(formats, list):
            raise UnexpectedResponseError(
                "yt-dlp returned invalid formats",
                provider="yt-dlp",
                operation="get_video_formats",
                details="formats_type",
            )
        
        media_id = info.get("id")

        if media_id is None:
            raise UnexpectedResponseError(
                "yt-dlp returned info without media id",
                provider="yt-dlp",
                operation="get_video_formats",
                details="missing_media_id",
            )

        result: list[AvailableVideoFormat] = []
        seen_heights: set[int] = set()

        for item in formats:
            if not isinstance(item, dict):
                continue

            format_id = item.get("format_id")
            height = item.get("height")
            vcodec = item.get("vcodec")

            if not isinstance(format_id, str):
                continue

            if not isinstance(height, int):
                continue

            if vcodec in (None, "none"):
                continue

            if height in seen_heights:
                continue

            seen_heights.add(height)

            result.append(
                AvailableVideoFormat(
                    video_id=media_id,
                    format_id=int(format_id),
                    height=height,
                )
            )

        if not result:
            raise EmptyResponseError(
                "yt-dlp returned no available video formats",
                provider="yt-dlp",
                operation="get_video_formats",
                details="formats",
            )

        return sorted(result, key=lambda item: item.height, reverse=True)
    
    async def get_video_formats(self, url: str) -> list[AvailableVideoFormat]:
        return await asyncio.to_thread(
            self._get_video_formats_sync,
            url,
        )