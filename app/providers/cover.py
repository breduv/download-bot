import asyncio
from logging import getLogger
from pathlib import Path

import aiohttp
from mutagen import MutagenError # pyright: ignore[reportPrivateImportUsage]
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3, ID3NoHeaderError # pyright: ignore[reportPrivateImportUsage]

from app.errors.provider import DownloadError, ProviderTimeoutError, UnexpectedResponseError


logger = getLogger(__name__)


class CoverProvider:
    async def download_cover(self, url: str, output_dir: Path, filename: str = "cover.jpg") -> Path:
        cover_path = output_dir / filename
        logger.debug("Cover download started filename=%s", filename)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise DownloadError(
                            f"cover request returned status {response.status}",
                            provider="cover",
                            operation="download_cover",
                        )

                    content = await response.read()

            if not content:
                raise DownloadError(
                    "cover response is empty",
                    provider="cover",
                    operation="download_cover",
                )

            cover_path.write_bytes(content)

        except DownloadError:
            raise

        except aiohttp.ClientError as exc:
            raise DownloadError(
                "cover download request failed",
                provider="cover",
                operation="download_cover",
            ) from exc

        except TimeoutError as exc:
            raise ProviderTimeoutError(
                "cover download timed out",
                provider="cover",
                operation="download_cover",
            ) from exc

        except OSError as exc:
            raise DownloadError(
                "failed to save cover",
                provider="cover",
                operation="download_cover",
            ) from exc

        logger.info("Cover downloaded size_bytes=%d", len(content))
        return cover_path
    
    def _set_mp3_cover(self, mp3_path: Path, cover_path: Path) -> None:
        try:
            try:
                tags = ID3(mp3_path)
            except ID3NoHeaderError:
                tags = ID3()

            tags.delall("APIC")

            tags.add(
                APIC(
                    encoding=3,
                    mime=self._detect_mime(cover_path),
                    type=3,
                    desc="Cover",
                    data=cover_path.read_bytes(),
                )
            )

            tags.save(mp3_path, v2_version=3)

        except (MutagenError, OSError) as exc:
            raise DownloadError(
                "failed to embed cover into mp3",
                provider="cover",
                operation="set_mp3_cover",
            ) from exc

    def _detect_mime(self, path: Path) -> str:
        match path.suffix.lower():
            case ".jpg" | ".jpeg":
                return "image/jpeg"
            case ".png":
                return "image/png"
            case ".webp":
                return "image/webp"
            case _:
                raise UnexpectedResponseError(
                    f"unsupported cover image extension: {path.suffix}",
                    provider="cover",
                    operation="set_mp3_cover",
                )
            
    async def set_mp3_cover(self, mp3_path: Path, cover_path: Path) -> None:
        await asyncio.to_thread(
            self._set_mp3_cover,
            mp3_path,
            cover_path,
        )
        logger.debug("MP3 cover embedded")

    def _set_mp3_metadata(self, mp3_path: Path, *, title: str, artist: str) -> None:
        try:
            try:
                tags = EasyID3(mp3_path)
            except ID3NoHeaderError:
                tags = EasyID3()
                tags.save(mp3_path)

            tags["title"] = title
            tags["artist"] = artist

            tags.save(mp3_path)
        except (MutagenError, OSError) as exc:
            raise DownloadError(
                "failed to set mp3 metadata",
                provider="cover",
                operation="set_mp3_metadata",
            ) from exc

    async def set_mp3_metadata(self, mp3_path: Path, *, title: str, artist: str) -> None:
        await asyncio.to_thread(
            self._set_mp3_metadata,
            mp3_path,
            title=title,
            artist=artist
        )
        logger.debug("MP3 metadata written")
