from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from app.audio.downloader import download_audio, fetch_thumbnail, download_video
from app.audio.search import search_spotify_url, search_tracks, search_youtube_video
from app.core.logger import get_logger
from app.core.utils import async_tempdir, create_inline_keyboard, is_spotify_url, is_url, is_youtube_video_url, is_tiktok_video_url


router = Router(name = "main")
logger = get_logger(__name__)

track_links = {}


@router.message(Command('start'), F.text)
async def start(msg: Message):
    await msg.answer("Привет!\nЯ бот для скачивания музыки с Spotify и видео-аудио с YouTube\nСкинь мне название песни или ссылку, и я всё сделаю")

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

            elif is_youtube_video_url(query):
                logger.debug(f"Received YouTube URL: {query}")
                qualities = await search_youtube_video(query)
                buttons = []
                for q in qualities:
                    buttons.append([(f"{q['height']}p", f"download|{q['format_id']}|{query}")])

                buttons.append([(f"audio", f"download|audio|{query}")])
                
                keyboard = create_inline_keyboard(buttons)
                await msg.answer("Выбери формат:", reply_markup=keyboard)

            elif is_tiktok_video_url(query):
                logger.debug(f"Received TikTok URL: {query}")
                fake_callback = CallbackQuery(
                    id='fake',
                    from_user=msg.from_user,
                    chat_instance='fake',
                    data=f"download|-1|{query}",
                    message=msg,
                )
                await download(fake_callback)


        else:

            results = await search_tracks(query=query, limit=10)

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
                query = f"{artist} - {title}"
                path = await download_audio(query, tmpdir)
                thumb = await fetch_thumbnail(track["cover"])
                if path:
                    await msg.delete()

                    logger.info(f"Sending track to user: {query}")

                    with open(path, "rb") as f:
                        data = f.read()
                    audio = BufferedInputFile(data, filename=f"{artist} - {title}.mp3")

                    await callback.message.answer_audio(audio=audio, title=title, performer=artist, thumbnail=thumb, request_timeout=300)
                else:
                    await callback.message.answer("Ошибка: трек не сохранился\nОбратитесь к @bread_dubov")
        else:
            await callback.message.answer("Ошибка: не удалось получить трек")
    elif callback.data.startswith("download|"):
        data = callback.data.split("|")
        # logger.debug(f"Download request received with data: {data}")
        format_id = data[1]
        url = data[2]
        async with async_tempdir() as tmpdir:
            if format_id == "audio":
                path = await download_audio(url, tmpdir)
            else:
                path = await download_video(url, int(format_id), tmpdir)
            if path:
                await msg.delete()

                logger.info(f"Sending video to user: {url}")

                with open(path, "rb") as f:
                    data = f.read()
                ext = path.rsplit('.', 1)[-1]
                video = BufferedInputFile(data, filename=f"video.{ext}")

                if format_id == "audio":
                    await callback.message.answer_audio(audio=video, request_timeout=300)
                else:
                    await callback.message.answer_video(video=video, request_timeout=300)
            else:
                await callback.message.answer("Ошибка: видео не сохранилось\nОбратитесь к @bread_dubov")

    return