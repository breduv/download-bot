import asyncio
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, YoutubeDLError

from app.core.config import Settings
from app.errors.providers import MediaNotFoundError, YtdlpProviderError
from app.models.media import DownloadedMedia, MediaFormat


class YtdlpProvider:
    def __init__(self, settings: Settings) -> None:
        self.base_options: dict[str, Any] = {
            "quiet": True,
            "no_warnings": False,
            "noplaylist": True
        }
        if settings.media_proxy:
            self.base_options["proxy"] = settings.media_proxy.get_secret_value()


    async def inspect(self, url: str) -> list[MediaFormat]:
        try:
            return await asyncio.to_thread(
                self._inspect_sync, 
                url
            )
        except (MediaNotFoundError, YtdlpProviderError):
            raise
        except YoutubeDLError as exc:
            raise YtdlpProviderError("Media inspection failed") from exc
        
    def _inspect_sync(self, url: str) -> list[MediaFormat]:
        with YoutubeDL(self.base_options) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            raise MediaNotFoundError(url)
        
        formats = info.get("formats") or []

        return [
            MediaFormat(
                format_id=str(item["format_id"]),
                extension=item.get("ext", ""),
                height=item.get("height"),
                fps=item.get("fps"),
                filesize=item.get("filesize") or item.get("filesize_approx"),
            )
            for item in formats
            if item.get("format_id")
            and item.get("vcodec") != "none"
        ]


    async def download_audio(self, query_or_url: str, output_dir: Path) -> DownloadedMedia:
        try:
            return await asyncio.to_thread(
                self._download_audio_sync,
                query_or_url,
                output_dir,
            )
        except (MediaNotFoundError, YtdlpProviderError):
            raise
        except YoutubeDLError as exc:
            raise YtdlpProviderError("Audio download failed") from exc
        
    def _download_audio_sync(self, query_or_url: str, output_dir: Path) -> DownloadedMedia:

        options = self.base_options | {
            "format": "bestaudio/best",
            "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

        target = (
            query_or_url
            if query_or_url.startswith(("http://", "https://"))
            else f"ytsearch1:{query_or_url}"
        )

        info = self._download(target, options)
        path = self._find_result(output_dir, {".mp3"})
        return self._build_result(path, info)


    async def download_video(self, url: str, format_id: str, output_dir: Path) -> DownloadedMedia:
        try:
            return await asyncio.to_thread(
                self._download_video_sync,
                url,
                format_id,
                output_dir,
            )
        except (MediaNotFoundError, YtdlpProviderError):
            raise
        except YoutubeDLError as exc:
            raise YtdlpProviderError("Video download failed") from exc
        
    def _download_video_sync(self, url: str, format_id: str, output_dir: Path) -> DownloadedMedia:
        options = self.base_options | {
            "format": f"{format_id}+bestaudio/{format_id}/best",
            "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
            "merge_output_format": "mp4",
            "recodevideo": "mp4",
        }

        info = self._download(url, options)
        path = self._find_result(output_dir, {".mp4"})
        return self._build_result(path, info)
    

    def _download(self, target: str, options: dict[str, Any]) -> dict:
        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(target, download=True)
        except DownloadError as exc:
            raise YtdlpProviderError(str(exc)) from exc

        if not info:
            raise MediaNotFoundError(target)

        if info.get("_type") == "playlist":
            entries = list(info.get("entries") or [])
            if not entries:
                raise MediaNotFoundError(target)
            info = entries[0]

        return info
    
    @staticmethod
    def _find_result(directory: Path, extensions: set[str]) -> Path:
        files = [
            path for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in extensions
        ]
        if not files:
            raise MediaNotFoundError("Output file was not created")
        return max(files, key=lambda path: path.stat().st_mtime)
    
    @staticmethod
    def _build_result(path: Path, info: dict) -> DownloadedMedia:
        duration = info.get("duration")
        return DownloadedMedia(
            path=path,
            title=info.get("title"),
            duration_seconds=int(duration) if duration is not None else None,
            filesize=path.stat().st_size,
        )
