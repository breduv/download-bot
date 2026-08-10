from logging import getLogger
from pathlib import Path

from app.providers.cover import CoverProvider
from app.providers.gallerydl import GallerydlProvider
from app.providers.spotify import SpotifyProvider
from app.providers.ytdlp import YtdlpProvider


logger = getLogger(__name__)


class DownloadService:
    def __init__(
        self,
        spotify_provider: SpotifyProvider,
        ytdlp_provider: YtdlpProvider,
        cover_provaider: CoverProvider,
        gallerydl_provider: GallerydlProvider,
    ) -> None:
        self.spotify_provider = spotify_provider
        self.ytdlp_provider = ytdlp_provider
        self.cover_provaider = cover_provaider
        self.gallerydl_provider = gallerydl_provider

    async def download_media(
        self,
        media: dict[str, str],
        output_dir: Path,
    ) -> tuple[Path, Path | None]:
        value = media.get("audio")

        if value is not None:
            logger.info("Audio download started metadata=%s", "title" in media and "artist" in media)
            audio_path, cover_path = await self.ytdlp_provider.download_audio(
                query_or_url=value,
                output_dir=output_dir,
            )

            title = media.get("title")
            artist = media.get("artist")

            if title is not None and artist is not None:
                await self.cover_provaider.set_mp3_metadata(audio_path, title=title, artist=artist)

            cover_url = media.get("cover_url")

            if cover_url is not None:
                cover_path = await self.cover_provaider.download_cover(cover_url, output_dir)

            if cover_path is not None:
                await self.cover_provaider.set_mp3_cover(audio_path, cover_path)

            logger.info("Audio download completed cover=%s", cover_path is not None)
            return audio_path, cover_path

        logger.info("Video download started")
        video_path = await self.ytdlp_provider.download_video(
            url=media["video"],
            output_dir=output_dir,
        )
        logger.info("Video download completed")
        return video_path, None

    async def download_photos(self, url: str, output_dir: Path) -> list[Path]:
        logger.info("Gallery download started")
        photo_paths = await self.gallerydl_provider.download_photos(
            url=url,
            output_dir=output_dir,
        )
        logger.info("Gallery download completed photos_count=%d", len(photo_paths))
        return photo_paths
    
    async def download_on_spotify(self, track_id: str, output_dir: Path) -> tuple[Path, Path | None]:
        logger.info("Spotify selection download started track_id=%s", track_id)
        track = await self.spotify_provider.get_track(track_id)

        audio_path, cover_path = await self.ytdlp_provider.download_audio(
            query_or_url=f"{track.artist} - {track.title}",
            output_dir=output_dir,
        )

        await self.cover_provaider.set_mp3_metadata(audio_path, title=track.title, artist=track.artist)

        if track.cover_url is not None:
            cover_path = await self.cover_provaider.download_cover(track.cover_url, output_dir)

        if cover_path is not None:
            await self.cover_provaider.set_mp3_cover(audio_path, cover_path)

        logger.info("Spotify selection download completed cover=%s", cover_path is not None)
        return audio_path, cover_path

    async def download_on_youtube(self, url: str, format_id: str, output_dir: Path) -> tuple[Path, Path | None]:
        logger.info("YouTube selection download started format_id=%s", format_id)
        if format_id == "-1":
            audio_path, cover_path = await self.ytdlp_provider.download_audio(url, output_dir)

            if cover_path is not None:
                await self.cover_provaider.set_mp3_cover(audio_path, cover_path)

            logger.info("YouTube audio download completed cover=%s", cover_path is not None)
            return audio_path, cover_path

        video_path = await self.ytdlp_provider.download_video(url, output_dir, format_id)
        logger.info("YouTube video download completed format_id=%s", format_id)
        return video_path, None
