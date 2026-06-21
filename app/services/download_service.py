from pathlib import Path
from typing import Literal

from app.errors.service import InvalidInputKindError
from app.models.download import MediaDownloadPayload
from app.providers.cover import CoverProvider
from app.providers.spotify import SpotifyProvider
from app.providers.ytdlp import YtdlpProvider


class DownloadService:
    def __init__(self, spotify_provider: SpotifyProvider, ytdlp_provider: YtdlpProvider, cover_provaider: CoverProvider) -> None:
        self.spotify_provider = spotify_provider
        self.ytdlp_provider = ytdlp_provider
        self.cover_provaider = cover_provaider

    async def download_media(self, media: dict[Literal["audio", "video", "cover_url"], str], output_dir: Path,) -> Path:
        value = media.get("audio")

        if value is not None:
            audio_path = await self.ytdlp_provider.download_audio(
                query_or_url=value,
                output_dir=output_dir,
            )
            cover_url = media.get("cover_url")
            if not cover_url:
                return audio_path
            
            cover_path = await self.cover_provaider.download_cover(cover_url, output_dir)
            await self.cover_provaider.set_mp3_cover(audio_path, cover_path)

            return audio_path
        
        value = media.get("video")

        if value is not None:
            return await self.ytdlp_provider.download_video(
                url=value,
                output_dir=output_dir,
            )
        
        raise InvalidInputKindError(
            "invalid media download payload",
            service="download",
            operation="download_media",
            details="invalid_download_payload",
        )