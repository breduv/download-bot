import asyncio

from spotipy.client import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

from app.core.config import Settings
from app.errors.providers import SpotifyProviderError
from app.models.media import TrackInfo


class SpotifyProvider:
    def __init__(self, settings: Settings) -> None:
        self._client = Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=settings.spotify_client_id,
                client_secret=settings.spotify_client_secret.get_secret_value()
            ),
            proxies={
                "http": settings.media_proxy.get_secret_value() if settings.media_proxy else None,
                "https": settings.media_proxy.get_secret_value() if settings.media_proxy else None,
            },
        )

    def _convert_track(self, item: dict) -> TrackInfo:
        images = item.get("album", {}).get("images", [])

        return TrackInfo(
            title=item["name"],
            artist=item["artists"][0]["name"],
            cover_url=images[0]["url"] if images else None,
            duration_seconds=item["duration_ms"] // 1000,
        )

    async def search_tracks(self, query: str, limit: int = 10) -> list[TrackInfo]:
        try:
            response = await asyncio.to_thread(
                self._client.search,
                q=query,
                type="track",
                limit=limit,
            )
        except Exception as exc:
            raise SpotifyProviderError("Spotify search failed") from exc

        items = response.get("tracks", {}).get("items", [])

        return [self._convert_track(item) for item in items]
    
    async def get_track(self, track_id: str) -> TrackInfo:
        try:
            item = await asyncio.to_thread(
                self._client.track,
                track_id,
            )
        except Exception as exc:
            raise SpotifyProviderError("Spotify get track failed") from exc

        return self._convert_track(item)