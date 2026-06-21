import asyncio
from logging import getLogger

from requests.exceptions import Timeout as RequestsTimeout
from spotipy.client import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

from app.core.config import Settings
from app.errors.provider import EmptyResponseError, ProviderTimeoutError, TrackFetchError
from app.models.media import TrackInfo


logger = getLogger(__name__)


class SpotifyProvider:
    def __init__(self, settings: Settings) -> None:
        self.client = Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=settings.spotify_client_id,
                client_secret=settings.spotify_client_secret.get_secret_value()
            ),
            proxies={
                "http": settings.media_proxy.get_secret_value() if settings.media_proxy else None,
                "https": settings.media_proxy.get_secret_value() if settings.media_proxy else None,
            },
            requests_timeout=20,
            retries=3,
        )

        self.search_limit = settings.search_limit

    def _convert_track(self, item: dict) -> TrackInfo:
        images = item["album"]["images"]

        return TrackInfo(
            title=item["name"],
            artist = ", ".join(artist["name"] for artist in item["artists"]),
            cover_url=images[0]["url"] if images else None,
            track_id=item["id"],
        )
    
    async def get_track(self, track_id_or_url: str) -> TrackInfo:
        logger.debug("Spotify get_track request started")
        try:
            item = await asyncio.to_thread(
                self.client.track,
                track_id_or_url,
            )
        except RequestsTimeout as exc:
            raise ProviderTimeoutError(
                "Spotify get track request timed out",
                provider="spotify",
                operation="get_track",
            ) from exc
        except Exception as exc:
            raise TrackFetchError(
                f"Spotify get track failed for id or url: {track_id_or_url}",
                provider="spotify",
                operation="get_track"
            ) from exc

        if item is None:
            raise EmptyResponseError(
                f"Spotify returned no track for id or url: {track_id_or_url}",
                provider="spotify",
                operation="get_track",
            )

        track = self._convert_track(item)
        logger.debug("Spotify get_track request completed track_id=%s", track.track_id)
        return track
    
    async def search_tracks(self, query: str) -> list[TrackInfo]:
        logger.debug("Spotify search request started query_length=%d", len(query))
        try:
            response = await asyncio.to_thread(
                self.client.search,
                q=query,
                type="track",
                limit=self.search_limit,
            )
        except RequestsTimeout as exc:
            raise ProviderTimeoutError(
                "Spotify search request timed out",
                provider="spotify",
                operation="search_tracks",
            ) from exc
        except Exception as exc:
            raise TrackFetchError(
                f"Spotify search failed for query: {query}",
                provider="spotify",
                operation="search_tracks"
            ) from exc

        if response is None:
            raise EmptyResponseError(
                f"Spotify search returned no response for query: {query}",
                provider="spotify",
                operation="search_tracks",
                details="response",
            )

        items = response["tracks"]["items"]

        if not items:
            raise EmptyResponseError(
                f"Spotify search returned no tracks for query: {query}",
                provider="spotify",
                operation="search_tracks",
                details="tracks",
            )

        tracks = [self._convert_track(item) for item in items]
        logger.debug("Spotify search request completed results_count=%d", len(tracks))
        return tracks
