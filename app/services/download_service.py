from pathlib import Path
from typing import Literal

from app.errors.service import InvalidInputKindError
from app.providers.spotify import SpotifyProvider
from app.providers.ytdlp import YtdlpProvider


class DownloadService:
    def __init__(self, spotify_provider: SpotifyProvider, ytdlp_provider: YtdlpProvider) -> None:
        self.spotify_provider = spotify_provider
        self.ytdlp_provider = ytdlp_provider

    async def download_media(self, media: dict[Literal["audio", "video"], str], output_dir: Path,) -> Path:
        media_type, value = next(iter(media.items()))

        match media_type:
            case "audio":
                return await self.ytdlp_provider.download_audio(
                    query_or_url=value,
                    output_dir=output_dir,
                )

            case "video":
                return await self.ytdlp_provider.download_video(
                    url=value,
                    output_dir=output_dir,
                )