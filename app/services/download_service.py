from pathlib import Path
from typing import Literal

from app.errors.service import InvalidInputKindError
from app.providers.cover import CoverProvider
from app.providers.spotify import SpotifyProvider
from app.providers.ytdlp import YtdlpProvider


class DownloadService:
    def __init__(self, spotify_provider: SpotifyProvider, ytdlp_provider: YtdlpProvider, cover_provaider: CoverProvider) -> None:
        self.spotify_provider = spotify_provider
        self.ytdlp_provider = ytdlp_provider
        self.cover_provaider = cover_provaider

    async def download_media(self, media: dict[str, str], output_dir: Path,) -> Path:
        value = media.get("audio")

        if value is not None:
            audio_path = await self.ytdlp_provider.download_audio(
                query_or_url=value,
                output_dir=output_dir,
            )

            title = media.get("title")
            artist = media.get("artist")

            if title is not None and artist is not None:
                await self.cover_provaider.set_mp3_metadata(audio_path, title=title, artist=artist)

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
    
    async def download_on_spotify(self, track_id: str, output_dir: Path) -> Path:
        track = await self.spotify_provider.get_track(track_id)

        audio_path = await self.ytdlp_provider.download_audio(
                query_or_url=f"{track.artist} - {track.title}",
                output_dir=output_dir,
            )
        
        await self.cover_provaider.set_mp3_metadata(audio_path, title=track.title, artist=track.artist)

        if track.cover_url is not None:
            cover_path = await self.cover_provaider.download_cover(track.cover_url, output_dir)
            await self.cover_provaider.set_mp3_cover(audio_path, cover_path)

        return audio_path
    
    async def download_on_youtube(self, url: str, format_id: str, output_dir: Path) -> Path:
        if format_id == "-1":
            return await self.ytdlp_provider.download_audio(url, output_dir)
        
        return await self.ytdlp_provider.download_video(url, output_dir, format_id)