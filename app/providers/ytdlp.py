import asyncio
from logging import getLogger
from pathlib import Path
from typing import Any, cast

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError as YtdlpDownloadError

from app.core.config import Settings
from app.errors.provider import DownloadError, EmptyResponseError, MediaTooLargeError, UnexpectedResponseError
from app.models.media import AvailableVideoFormat


logger = getLogger(__name__)


class YtdlpProvider:
    def __init__(self, settings: Settings) -> None:
        self.base_options: dict[str, Any] = {
            "quiet": True,
            "no_warnings": False,
            "noplaylist": True,
            "noprogress": True,
        }
        if settings.media_proxy:
            self.base_options["proxy"] = settings.media_proxy.get_secret_value()
        
        self.max_upload_size_bytes = settings.max_upload_size_mb * 1024 * 1024

    def _download(self, target: str, options: dict[str, Any], operation: str) -> dict[str, Any]:
        logger.debug(
            "yt-dlp extraction started operation=%s target_type=%s",
            operation,
            "url" if target.startswith(("http://", "https://")) else "search",
        )
        try:
            with YoutubeDL(options) as ydl: # pyright: ignore[reportArgumentType]
                raw_info = ydl.extract_info(target, download=True)

                if raw_info is None:
                    raise EmptyResponseError(
                        "yt-dlp returned empty response",
                        provider="yt-dlp",
                        operation=operation,
                    )
                    
                info = ydl.sanitize_info(raw_info)

        except YtdlpDownloadError as exc:
            raise DownloadError(
                "yt-dlp failed to download target",
                provider="yt-dlp",
                operation=operation,
            ) from exc

        if not isinstance(info, dict):
            raise UnexpectedResponseError(
                f"yt-dlp returned unexpected response type: {type(info).__name__}",
                provider="yt-dlp",
                operation=operation,
            )
        
        entries = info.get("entries")

        if entries is None:
            logger.debug("yt-dlp extraction completed operation=%s", operation)
            return cast(dict[str, Any], info)

        if not isinstance(entries, list):
            raise UnexpectedResponseError(
                "yt-dlp returned invalid entries",
                provider="yt-dlp",
                operation=operation,
            )

        if len(entries) == 0:
            raise EmptyResponseError(
                "yt-dlp returned empty entries",
                provider="yt-dlp",
                operation=operation,
                details="entries",
            )

        entry = entries[0]

        if not isinstance(entry, dict):
            raise UnexpectedResponseError(
                "yt-dlp returned invalid entry",
                provider="yt-dlp",
                operation=operation,
            )

        logger.debug("yt-dlp extraction completed operation=%s", operation)
        return cast(dict[str, Any], entry)
    
    def _download_audio_sync(self, query_or_url: str, output_dir: Path) -> tuple[Path, Path | None]:
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
                # {
                #     "key": "EmbedThumbnail",
                # },
            ],
        }

        target = (
            query_or_url
            if query_or_url.startswith(("http://", "https://"))
            else f"ytsearch1:{query_or_url}"
        )

        info = self._download(target, options, operation="download_audio")

        media_id = info.get("id")
        if media_id is None:
            raise UnexpectedResponseError(
                "yt-dlp returned info without media id",
                provider="yt-dlp",
                operation="download_audio",
            )

        file_path = output_dir / (media_id+".mp3")
        if not file_path.is_file():
            raise DownloadError(
                "downloaded file was not found",
                provider="yt-dlp",
                operation="download_audio",
            )

        filesize = file_path.stat().st_size
        
        if filesize > self.max_upload_size_bytes:
            raise MediaTooLargeError(
                "downloaded media file is too large",
                provider="yt-dlp",
                operation="download_audio",
            )
        
        cover_path = None
        
        for suffix in (".jpg", ".jpeg", ".png", ".webp"):
            candidate = output_dir / f"{media_id}{suffix}"

            if candidate.is_file():
                cover_path = candidate
                break

        logger.info(
            "Audio file prepared media_id=%s size_bytes=%d cover=%s",
            media_id,
            filesize,
            cover_path is not None,
        )
        return file_path, cover_path
    
    async def download_audio(self, query_or_url: str, output_dir: Path) -> tuple[Path, Path | None]:
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

        info = self._download(url, options, operation="download_video")

        media_id = info.get("id")
        if media_id is None:
            raise UnexpectedResponseError(
                "yt-dlp returned info without media id",
                provider="yt-dlp",
                operation="download_video",
            )

        file_path = output_dir / (media_id+".mp4")
        if not file_path.is_file():
            raise DownloadError(
                "downloaded file was not found",
                provider="yt-dlp",
                operation="download_video",
            )

        filesize = file_path.stat().st_size
        
        if filesize > self.max_upload_size_bytes:
            raise MediaTooLargeError(
                "downloaded media file is too large",
                provider="yt-dlp",
                operation="download_video",
                details="selected_format" if format_id is not None else "",
            )

        logger.info(
            "Video file prepared media_id=%s size_bytes=%d format_id=%s",
            media_id,
            filesize,
            format_id or "auto",
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
            )

        formats = info.get("formats")

        if not isinstance(formats, list):
            raise UnexpectedResponseError(
                "yt-dlp returned invalid formats",
                provider="yt-dlp",
                operation="get_video_formats",
            )
        
        media_id = info.get("id")

        if media_id is None:
            raise UnexpectedResponseError(
                "yt-dlp returned info without media id",
                provider="yt-dlp",
                operation="get_video_formats",
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
                    format_id=format_id,
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

        logger.debug("Video formats extracted formats_count=%d", len(result))
        return sorted(result, key=lambda item: item.height, reverse=True)
    
    async def get_video_formats(self, url: str) -> list[AvailableVideoFormat]:
        return await asyncio.to_thread(
            self._get_video_formats_sync,
            url,
        )
