import asyncio
from pathlib import Path

import aiofiles
import aiohttp

from app.errors.providers import MediaNotFoundError, ThumbnailProviderError
from app.models.media import DownloadedImage


class ThumbnailProvider:
    _EXTENSIONS = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }

    def __init__(self, session: aiohttp.ClientSession, max_size: int = 5 * 1024 * 1024, timeout: float = 10) -> None:
        self._session = session
        self._max_size = max_size
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def download(self, url: str, output_dir: Path) -> DownloadedImage:
        try:
            async with self._session.get(url, timeout=self._timeout) as response:
                if response.status == 404:
                    raise MediaNotFoundError(url)

                response.raise_for_status()

                content_type = (
                    response.headers
                    .get("Content-Type", "")
                    .split(";", 1)[0]
                    .lower()
                )
                extension = self._EXTENSIONS.get(content_type)

                if extension is None:
                    raise ThumbnailProviderError(f"Unsupported content type: {content_type}")

                content_length = response.content_length
                if content_length is not None and content_length > self._max_size:
                    raise ThumbnailProviderError("Thumbnail is too large")

                path = output_dir / f"thumbnail{extension}"
                downloaded = 0

                async with aiofiles.open(path, "wb") as file:
                    async for chunk in response.content.iter_chunked(64 * 1024):
                        downloaded += len(chunk)

                        if downloaded > self._max_size:
                            raise ThumbnailProviderError("Thumbnail is too large")

                        await file.write(chunk)

                return DownloadedImage(path=path, mime_type=content_type)

        except (MediaNotFoundError, ThumbnailProviderError):
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise ThumbnailProviderError("Thumbnail download failed") from exc