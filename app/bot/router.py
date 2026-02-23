from aiogram import Router
from aiogram.types import Message, CallbackQuery, FSInputFile

from app.audio.downloader import download_audio, fetch_thumbnail
from app.audio.search import search_spotify_url, search_tracks
from app.core.logger import get_logger
from app.core.utils import async_tempdir, create_inline_keyboard, is_spotify_url, is_url


router = Router(name = "main")
logger = get_logger(__name__)

track_links = {}

@router.message()
async def search(msg: Message):
    assert msg.text and msg.from_user is not None
    if msg.chat.id == msg.from_user.id:
        query = msg.text.strip()

        if is_url(query):
            if is_spotify_url(query):
                logger.debug(f"Received Spotify URL: {query}")
                track = await search_spotify_url(query)
                if not track:
                    logger.error(f"Failed to find track for Spotify URL: {query}")
                    await msg.answer("Ошибка: не удалось найти трек по Spotify URL")
                    return
                fake_callback = CallbackQuery(
                    id='fake',
                    from_user=msg.from_user,
                    chat_instance='fake',
                    data=f"track_{str(len(track_links)+1)}",
                    message=msg,
                )
                track_links[str(len(track_links)+1)] = track
                await download(fake_callback)

        else:

            results = await search_tracks(query)

            if not results:
                await msg.answer("Ничего не найдено :(")
                return

            buttons = []
            for idx, track in enumerate(results, 1):
                track_links[str(idx)] = track # сохраняем ссылку
                buttons.append([(f"{track['artist']} – {track['title']}", f"track_{idx}")])

            keyboard = create_inline_keyboard(buttons)
            await msg.answer("Выбери трек:", reply_markup=keyboard)

@router.callback_query()
async def download(callback: CallbackQuery):
    assert callback.data and callback.message is not None
    msg = await callback.message.answer("Скачиваю...")
    if callback.data.startswith("track_"):
        idx = callback.data.split("_")[1]
        track = track_links.get(idx)
        if track:
            title = track['title']
            artist = track['artist']
            
            async with async_tempdir() as tmpdir:
                logger.debug(f"Downloading track: {artist} - {title}")
                query = f"{artist} - {title}"
                path = await download_audio(query, tmpdir)
                thumb = await fetch_thumbnail(track["cover"])
                if path:
                    await msg.delete()
                    await callback.message.answer_audio(audio=FSInputFile(path), title=title, performer=artist, thumbnail=thumb)
                else:
                    await callback.message.answer("Ошибка: трек не сохранилось или потерялся путь")
        else:
            await callback.message.answer("Ошибка: не удалось получить трек")