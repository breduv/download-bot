import asyncio
from logging import getLogger
from pathlib import Path
from threading import Lock

from gallery_dl import config, exception, job

from app.core.config import Settings
from app.errors.provider import (
    DownloadError,
    EmptyResponseError,
    MediaTooLargeError,
)


logger = getLogger(__name__)


class GallerydlProvider:
    _config_lock = Lock()

    def __init__(self, settings: Settings) -> None:
        self.proxy = (
            settings.media_proxy.get_secret_value()
            if settings.media_proxy is not None
            else None
        )
        self.max_upload_size_bytes = settings.max_upload_size_mb * 1024 * 1024

    def _download_photos_sync(self, url: str, output_dir: Path) -> list[Path]:
        options: list[tuple[tuple[str, ...], str, object]] = [
            ((), "base-directory", str(output_dir)),
            ((), "directory", ()),
            (("extractor", "tiktok"), "photos", True),
            (("extractor", "tiktok"), "audio", False),
            (("extractor", "tiktok"), "videos", False),
            (("extractor", "tiktok"), "covers", False),
        ]

        if self.proxy is not None:
            options.append((("extractor", "tiktok"), "proxy", self.proxy))

        logger.debug(
            "Gallery-dl gallery download started proxy=%s",
            self.proxy is not None,
        )

        try:
            with self._config_lock, config.apply(options):
                status = job.DownloadJob(url).run()
        except exception.NoExtractorError as exc:
            raise DownloadError(
                "gallery-dl has no extractor for URL",
                provider="gallery-dl",
                operation="download_photos",
                details="unsupported_url",
            ) from exc
        except exception.GalleryDLException as exc:
            raise DownloadError(
                "gallery-dl failed to initialize download",
                provider="gallery-dl",
                operation="download_photos",
                details="initialization",
            ) from exc
        except OSError as exc:
            raise DownloadError(
                "gallery-dl failed to access output directory",
                provider="gallery-dl",
                operation="download_photos",
                details="filesystem",
            ) from exc

        if status:
            raise DownloadError(
                f"gallery-dl download failed with status {status}",
                provider="gallery-dl",
                operation="download_photos",
                details=f"status_{status}",
            )

        try:
            files = sorted(
                path
                for path in output_dir.rglob("*")
                if path.is_file() and not path.name.endswith(".part")
            )
        except OSError as exc:
            raise DownloadError(
                "failed to locate downloaded photo",
                provider="gallery-dl",
                operation="download_photos",
                details="filesystem",
            ) from exc

        if not files:
            raise EmptyResponseError(
                "gallery-dl did not download a photo",
                provider="gallery-dl",
                operation="download_photos",
                details="files",
            )

        total_size_bytes = 0

        for photo_path in files:
            try:
                size_bytes = photo_path.stat().st_size
            except OSError as exc:
                raise DownloadError(
                    "failed to inspect downloaded photo",
                    provider="gallery-dl",
                    operation="download_photos",
                    details="filesystem",
                ) from exc

            if size_bytes == 0:
                raise EmptyResponseError(
                    "gallery-dl downloaded an empty photo",
                    provider="gallery-dl",
                    operation="download_photos",
                    details="empty_file",
                )

            if size_bytes > self.max_upload_size_bytes:
                raise MediaTooLargeError(
                    "downloaded photo is too large",
                    provider="gallery-dl",
                    operation="download_photos",
                    details="upload_limit",
                )

            total_size_bytes += size_bytes

        logger.info(
            "Gallery-dl gallery download completed photos_count=%d total_size_bytes=%d",
            len(files),
            total_size_bytes,
        )
        return files

    async def download_photos(self, url: str, output_dir: Path) -> list[Path]:
        return await asyncio.to_thread(
            self._download_photos_sync,
            url,
            output_dir,
        )
