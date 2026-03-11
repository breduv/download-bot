import asyncio
from yt_dlp import YoutubeDL

from app.core.config import settings
from app.core.logger import get_logger
from app.core.utils import extract_spotify_track_id, similarity


logger = get_logger(__name__)

async def search_spotify_url(url: str) -> dict[str, str] | None:
    try:
        SP = settings.authorization
        track = SP.track(extract_spotify_track_id(url))
    except Exception as e:
        logger.error(f"Error searching Spotify URL: {e}")
        return None
    if track:
        logger.info('Found track for Spotify URL')
        return {
            'title': track['name'],
            'artist': track['artists'][0]['name'],
            'cover': track['album']['images'][0]['url'],
            'duration': track['duration_ms'] // 1000
        }
    return None

async def search_tracks(query: str, limit: int = 5) -> list[dict[str, str]]:
    SP = settings.authorization
    track_res = SP.search(q=query, type='track', limit=limit)
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

async def search_youtube_video(url: str):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        'proxy': settings.PROXY,
    }

    def _extract():
        with YoutubeDL(ydl_opts) as ydl: # type: ignore
            return ydl.extract_info(url, download=False)
    
    info = await asyncio.to_thread(_extract)
    formats = info.get("formats", [])
    result = []

    for f in formats: # type: ignore
        # Берём только форматы, где есть видео
        if f.get("vcodec") == "none":
            continue

        height = f.get("height")
        # logger.debug(f"Found format: {f.get('format_id')} with height: {height}")
        if not height:
            continue

        result.append({
            "format_id": f.get("format_id"),
            "ext": f.get("ext"),
            "height": height,
            "resolution": f.get("resolution") or f"{height}p",
            "fps": f.get("fps"),
            "vcodec": f.get("vcodec"),
            "acodec": f.get("acodec"),
            "filesize": f.get("filesize"),
            "tbr": f.get("tbr"),
        })

    # Убираем дубли по качеству, если хочешь только одно значение на 144p/240p/360p/...
    best_by_height = {}
    for fmt in result:
        h = fmt["height"]
        current = best_by_height.get(h)

        # выбираем лучший вариант внутри одного height
        if current is None:
            best_by_height[h] = fmt
        else:
            current_score = (current.get("tbr") or 0, current.get("fps") or 0)
            new_score = (fmt.get("tbr") or 0, fmt.get("fps") or 0)
            if new_score > current_score:
                best_by_height[h] = fmt

    # От максимального к минимальному
    return sorted(best_by_height.values(), key=lambda x: x["height"], reverse=True)