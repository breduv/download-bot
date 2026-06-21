from logging import getLogger
from urllib.parse import urlparse

from app.errors.service import EmptyQueryError, InvalidInputKindError, UnsupportedUrlError
from app.models.search import SPOTIFY_HOSTS, TIKTOK_HOSTS, YOUTUBE_HOSTS, YOUTUBE_MUSIC_HOSTS, InputKind, ParsedInput
from app.providers.spotify import SpotifyProvider
from app.providers.ytdlp import YtdlpProvider


logger = getLogger(__name__)


class SearchService:
    def __init__(self, spotify_provider: SpotifyProvider, ytdlp_provider: YtdlpProvider) -> None:
        self.spotify_provider = spotify_provider
        self.ytdlp_provider = ytdlp_provider

    def _parse_input(self, text: str) -> ParsedInput:
        value = text.strip()

        if not value:
            raise EmptyQueryError(
                "search query is empty",
                service="search",
            )

        parsed = urlparse(value)

        if parsed.scheme not in ("http", "https") and not parsed.netloc:
            return ParsedInput(InputKind.QUERY, value)
        
        host = parsed.hostname

        if host is None:
            raise UnsupportedUrlError(
                f"URL without host: {value}",
                service="search",
            )

        if host in SPOTIFY_HOSTS:
            return ParsedInput(InputKind.SPOTIFY, value)
        if host in YOUTUBE_HOSTS:
            return ParsedInput(InputKind.YOUTUBE, value)
        if host in YOUTUBE_MUSIC_HOSTS:
            return ParsedInput(InputKind.AUDIO, value)
        if host in TIKTOK_HOSTS:
            return ParsedInput(InputKind.VIDEO, value)

        return ParsedInput(InputKind.UNSUPPORTED_URL, value)
    
    async def search(self, text: str) -> dict[str, str]:
        parsed_input = self._parse_input(text)
        logger.debug("Search input parsed source=%s", parsed_input.source)

        if parsed_input.source == InputKind.QUERY:
            results = await self.spotify_provider.search_tracks(parsed_input.query)
            logger.info("Spotify search completed results_count=%d", len(results))
            return {
                f"sp:{track.track_id}": f"{track.artist} - {track.title}"
                for track in results
            }

        if parsed_input.source == InputKind.YOUTUBE:
            formats = await self.ytdlp_provider.get_video_formats(parsed_input.query)
            logger.info("YouTube formats loaded formats_count=%d", len(formats))

            video_id = formats[0].video_id

            results = {
                f"yt:{video.video_id}:{video.format_id}": f"{video.height}p"
                for video in formats
            }
            results[f"yt:{video_id}:-1"] = "Только звук"

            return results
        
        if parsed_input.source == InputKind.SPOTIFY:
            track = await self.spotify_provider.get_track(parsed_input.query)
            logger.info("Spotify track resolved track_id=%s", track.track_id)
            result = {
                "audio": f"{track.artist} - {track.title}",
                "title": track.title,
                "artist": track.artist
            }

            cover_url = track.cover_url
            if cover_url:
                result["cover_url"] = cover_url
            return result
        
        if parsed_input.source == InputKind.AUDIO:
            return {
                "audio": parsed_input.query
            }

        if parsed_input.source == InputKind.VIDEO:
            return {
                "video": parsed_input.query
            }
        
        if parsed_input.source == InputKind.UNSUPPORTED_URL:
            raise UnsupportedUrlError(
                f"unsupported url: {parsed_input.query}",
                service="search",
            )

        raise InvalidInputKindError(
            f"invalid input kind: {parsed_input.source}",
            service="search",
        )
