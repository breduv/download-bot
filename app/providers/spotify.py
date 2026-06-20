import asyncio

from spotipy.client import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

from app.core.config import Settings
from app.errors.provider import EmptyResponseError, TrackFetchError
from app.models.media import TrackInfo


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
        )

        self.search_limit = settings.search_limit

    def _convert_track(self, item: dict) -> TrackInfo:
        return TrackInfo(
            title=item["name"],
            artist = ", ".join(artist["name"] for artist in item["artists"]),
            cover_url=item["album"]["images"][0]["url"],
            track_id=item["id"],
        )
    
    async def get_track(self, track_id_or_url: str) -> TrackInfo:
        try:
            item = await asyncio.to_thread(
                self.client.track,
                track_id_or_url,
            )
        except Exception as exc:
            raise TrackFetchError(
                f"Spotify get track failed for id or url: {track_id_or_url}",
                provider="spotify",
                operation="get_track"
            ) from exc

        if item is None:
            raise EmptyResponseError(
                f"Track not found for id or url: {track_id_or_url}",
                provider="spotify",
                operation="get_track"
            )

        return self._convert_track(item)
    
    async def search_tracks(self, query: str) -> list[TrackInfo]:
        try:
            response = await asyncio.to_thread(
                self.client.search,
                q=query,
                type="track",
                limit=self.search_limit,
            )
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
                operation="search_tracks"
            )

        items = response["tracks"]["items"]

        return [self._convert_track(item) for item in items]