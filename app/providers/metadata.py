import asyncio

from mutagen.id3 import APIC, ID3, ID3NoHeaderError

from app.errors.providers import AudioMetadataProviderError
from app.models.media import DownloadedImage, DownloadedMedia


class AudioMetadataProvider:
    async def embed_cover(self, audio: DownloadedMedia, cover: DownloadedImage) -> None:
        try:
            await asyncio.to_thread(
                self._embed_cover_sync,
                audio,
                cover,
            )
        except Exception as exc:
            raise AudioMetadataProviderError("Failed to embed audio cover") from exc

    def _embed_cover_sync(self, audio: DownloadedMedia, cover: DownloadedImage) -> None:
        try:
            tags = ID3(audio.path)
        except ID3NoHeaderError:
            tags = ID3()

        # Удаляем старые встроенные обложки.
        tags.delall("APIC")

        tags.add(
            APIC(
                encoding=3,
                mime=cover.mime_type,
                type=3,  # Front cover
                desc="Cover",
                data=cover.path.read_bytes(),
            )
        )

        tags.save(audio.path, v2_version=3)