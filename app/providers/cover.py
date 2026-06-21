import asyncio
from pathlib import Path

import aiohttp
from mutagen import MutagenError # pyright: ignore[reportPrivateImportUsage]
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3, ID3NoHeaderError # pyright: ignore[reportPrivateImportUsage]

from app.errors.provider import DownloadError, UnexpectedResponseError


class CoverProvider:
    async def download_cover(self, url: str, output_dir: Path, filename: str = "cover.jpg") -> Path:
        cover_path = output_dir / filename

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise DownloadError(
                            "failed to download cover",
                            provider="cover",
                            operation="download_cover",
                            details="bad_status",
                        )

                    content = await response.read()

            if not content:
                raise DownloadError(
                    "cover response is empty",
                    provider="cover",
                    operation="download_cover",
                    details="empty_response",
                )

            cover_path.write_bytes(content)

        except DownloadError:
            raise

        except aiohttp.ClientError as exc:
            raise DownloadError(
                "cover download request failed",
                provider="cover",
                operation="download_cover",
                details="request_failed",
            ) from exc

        except TimeoutError as exc:
            raise DownloadError(
                "cover download timed out",
                provider="cover",
                operation="download_cover",
                details="timeout",
            ) from exc

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

        except MutagenError as exc:
            raise DownloadError(
                "failed to embed cover into mp3",
                provider="cover",
                operation="set_mp3_cover",
                details="mutagen_failed",
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
                    details="unsupported_cover_extension",
                )
            
    async def set_mp3_cover(self, mp3_path: Path, cover_path: Path) -> None:
        await asyncio.to_thread(
            self._set_mp3_cover,
            mp3_path,
            cover_path,
        )

    def _set_mp3_metadata(self, mp3_path: Path, *, title: str, artist: str) -> None:
        try:
            tags = EasyID3(mp3_path)
        except ID3NoHeaderError:
            tags = EasyID3()
            tags.save(mp3_path)

        tags["title"] = title
        tags["artist"] = artist

        tags.save(mp3_path)

    async def set_mp3_metadata(self, mp3_path: Path, *, title: str, artist: str) -> None:
        await asyncio.to_thread(
            self._set_mp3_metadata,
            mp3_path,
            title=title,
            artist=artist
        )