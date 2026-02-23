from app.core.config import settings
from app.core.utils import extract_spotify_track_id, similarity
from app.core.logger import get_logger


logger = get_logger(__name__)

SP = settings.authorization

async def search_spotify_url(url: str) -> dict[str, str] | None:
    try:
        track = SP.track(extract_spotify_track_id(url))
    except Exception as e:
        logger.error(f"Error searching Spotify URL: {e}")
        return None
    if track:
        return {
            'title': track['name'],
            'artist': track['artists'][0]['name'],
            'cover': track['album']['images'][0]['url'],
            'duration': track['duration_ms'] // 1000
        }
    return None

async def search_tracks(query: str, limit: int = 5) -> list[dict[str, str]]:
    track_res = SP.search(q=query, type='track', limit=10)
    items = track_res.get('tracks', {}).get('items', []) if track_res else []

    sorted_items = sorted(
        items,
        key=lambda track: similarity(query, f"{track['artists'][0]['name']} {track['name']}"),
        reverse=True
    )

    top_items = sorted_items[:limit]

    return [
        {
            'title': track['name'],
            'artist': track['artists'][0]['name'],
            'cover': track['album']['images'][0]['url'],
            'duration': track['duration_ms'] // 1000
        }
        for track in top_items
    ]