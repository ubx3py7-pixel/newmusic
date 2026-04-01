import asyncio
import os
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls import PyTgCalls
from pytgcalls.exceptions import (
    CallBusy as AlreadyJoinedError,
    NoActiveGroupCall,
    MTProtoClientNotConnected as TelegramServerError,
)
from pytgcalls.types import (
    Update,
    MediaStream,
    AudioQuality,
    VideoQuality,
    StreamEnded,
)

import config
from AnglePriyaMusic import LOGGER, YouTube, nand
from AnglePriyaMusic.misc import db
from AnglePriyaMusic.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from AnglePriyaMusic.utils.exceptions import AssistantErr
from AnglePriyaMusic.utils.formatters import check_duration, seconds_to_min, speed_converter
from AnglePriyaMusic.utils.inline.play import stream_markup
from AnglePriyaMusic.utils.stream.autoclear import auto_clean
from AnglePriyaMusic.utils.thumbnails import get_thumb
from strings import get_string

autoend = {}
counter = {}


def _make_stream(path, video=False, ffmpeg_params=None):
    """Helper to build MediaStream with correct params."""
    kwargs = dict(audio_quality=AudioQuality.HIGH)
    if video:
        kwargs["video_quality"] = VideoQuality.SD_480p
    if ffmpeg_params:
        kwargs["ffmpeg_parameters"] = ffmpeg_params
    return MediaStream(path, **kwargs)


async def _clear_(chat_id):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)


class Call(PyTgCalls):
    def __init__(self):
        self.userbot1 = Client(
            name="AnglePriyaAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
        )
        self.one = PyTgCalls(self.userbot1, cache_duration=100)

        self.userbot2 = Client(
            name="AnglePriyaAss2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
        )
        self.two = PyTgCalls(self.userbot2, cache_duration=100)

        self.userbot3 = Client(
            name="AnglePriyaAss3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
        )
        self.three = PyTgCalls(self.userbot3, cache_duration=100)

        self.userbot4 = Client(
            name="AnglePriyaAss4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
        )
        self.four = PyTgCalls(self.userbot4, cache_duration=100)

        self.userbot5 = Client(
            name="AnglePriyaAss5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
        )
        self.five = PyTgCalls(self.userbot5, cache_duration=100)

    @property
    def _clients(self):
        return [self.one, self.two, self.three, self.four, self.five]

    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause_stream(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume_stream(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            await _clear_(chat_id)
            await assistant.leave_group_call(chat_id)
        except:
            pass

    async def stop_stream_force(self, chat_id: int):
        strings = [config.STRING1, config.STRING2, config.STRING3, config.STRING4, config.STRING5]
        for string, client in zip(strings, self._clients):
            try:
                if string:
                    await client.leave_group_call(chat_id)
            except:
                pass
        try:
            await _clear_(chat_id)
        except:
            pass

    async def speedup_stream(self, chat_id: int, file_path, speed, playing):
        assistant = await group_assistant(self, chat_id)
        if str(speed) != "1.0":
            base = os.path.basename(file_path)
            chatdir = os.path.join(os.getcwd(), "playback", str(speed))
            os.makedirs(chatdir, exist_ok=True)
            out = os.path.join(chatdir, base)
            if not os.path.isfile(out):
                vs = {"0.5": 2.0, "0.75": 1.35, "1.5": 0.68, "2.0": 0.5}.get(str(speed), 1.0)
                proc = await asyncio.create_subprocess_shell(
                    f"ffmpeg -i {file_path} -filter:v setpts={vs}*PTS -filter:a atempo={speed} {out}",
                    stdin=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
        else:
            out = file_path

        dur = await asyncio.get_event_loop().run_in_executor(None, check_duration, out)
        dur = int(dur)
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration = seconds_to_min(dur)
        video = playing[0]["streamtype"] == "video"
        stream = _make_stream(out, video=video, ffmpeg_params=f"-ss {played} -to {duration}")

        if str(db[chat_id][0]["file"]) == str(file_path):
            await assistant.change_stream(chat_id, stream)
        else:
            raise AssistantErr("Umm")

        if str(db[chat_id][0]["file"]) == str(file_path):
            exis = (playing[0]).get("old_dur")
            if not exis:
                db[chat_id][0]["old_dur"] = db[chat_id][0]["dur"]
                db[chat_id][0]["old_second"] = db[chat_id][0]["seconds"]
            db[chat_id][0]["played"] = con_seconds
            db[chat_id][0]["dur"] = duration
            db[chat_id][0]["seconds"] = dur
            db[chat_id][0]["speed_path"] = out
            db[chat_id][0]["speed"] = speed

    async def force_stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            check.pop(0)
        except:
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        try:
            await assistant.leave_group_call(chat_id)
        except:
            pass

    async def skip_stream(
        self,
        chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        stream = _make_stream(link, video=bool(video))
        await assistant.change_stream(chat_id, stream)

    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        assistant = await group_assistant(self, chat_id)
        stream = _make_stream(
            file_path,
            video=(mode == "video"),
            ffmpeg_params=f"-ss {to_seek} -to {duration}",
        )
        await assistant.change_stream(chat_id, stream)

    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOGGER_ID)
        await assistant.join_group_call(config.LOGGER_ID, MediaStream(link))
        await asyncio.sleep(0.2)
        await assistant.leave_group_call(config.LOGGER_ID)

    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        language = await get_lang(chat_id)
        _ = get_string(language)
        stream = _make_stream(link, video=bool(video))
        try:
            await assistant.join_group_call(chat_id, stream)
        except NoActiveGroupCall:
            raise AssistantErr(_["call_8"])
        except AlreadyJoinedError:
            raise AssistantErr(_["call_9"])
        except TelegramServerError:
            raise AssistantErr(_["call_10"])
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)
        if await is_autoend():
            counter[chat_id] = {}
            users = len(await assistant.get_participants(chat_id))
            if users == 1:
                autoend[chat_id] = datetime.now() + timedelta(minutes=1)

    async def change_stream(self, client, chat_id):
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        try:
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
            await auto_clean(popped)
            if not check:
                await _clear_(chat_id)
                return await client.leave_group_call(chat_id)
        except:
            try:
                await _clear_(chat_id)
                return await client.leave_group_call(chat_id)
            except:
                return
        else:
            queued = check[0]["file"]
            language = await get_lang(chat_id)
            _ = get_string(language)
            title = (check[0]["title"]).title()
            user = check[0]["by"]
            original_chat_id = check[0]["chat_id"]
            streamtype = check[0]["streamtype"]
            videoid = check[0]["vidid"]
            db[chat_id][0]["played"] = 0
            exis = (check[0]).get("old_dur")
            if exis:
                db[chat_id][0]["dur"] = exis
                db[chat_id][0]["seconds"] = check[0]["old_second"]
                db[chat_id][0]["speed_path"] = None
                db[chat_id][0]["speed"] = 1.0
            video = str(streamtype) == "video"

            async def _send_now_playing(img_url, caption_args, markup_type="stream"):
                button = stream_markup(_, chat_id)
                run = await nand.send_photo(
                    chat_id=original_chat_id,
                    photo=img_url,
                    caption=_["stream_1"].format(*caption_args),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = markup_type

            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0:
                    return await nand.send_message(original_chat_id, text=_["call_6"])
                stream = _make_stream(link, video=video)
                try:
                    await client.change_stream(chat_id, stream)
                except Exception:
                    return await nand.send_message(original_chat_id, text=_["call_6"])
                img = await get_thumb(videoid)
                await _send_now_playing(
                    img,
                    [f"https://t.me/{nand.username}?start=info_{videoid}", title[:23], check[0]["dur"], user],
                    "tg",
                )

            elif "vid_" in queued:
                mystic = await nand.send_message(original_chat_id, _["call_7"])
                try:
                    file_path, direct = await YouTube.download(
                        videoid, mystic, videoid=True,
                        video=str(streamtype) == "video",
                    )
                except:
                    return await mystic.edit_text(_["call_6"], disable_web_page_preview=True)
                stream = _make_stream(file_path, video=video)
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    return await nand.send_message(original_chat_id, text=_["call_6"])
                img = await get_thumb(videoid)
                await mystic.delete()
                await _send_now_playing(
                    img,
                    [f"https://t.me/{nand.username}?start=info_{videoid}", title[:23], check[0]["dur"], user],
                )

            elif "index_" in queued:
                stream = _make_stream(videoid, video=video)
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    return await nand.send_message(original_chat_id, text=_["call_6"])
                button = stream_markup(_, chat_id)
                run = await nand.send_photo(
                    chat_id=original_chat_id,
                    photo=config.STREAM_IMG_URL,
                    caption=_["stream_2"].format(user),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"

            else:
                stream = _make_stream(queued, video=video)
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    return await nand.send_message(original_chat_id, text=_["call_6"])
                if videoid == "telegram":
                    photo = config.TELEGRAM_AUDIO_URL if str(streamtype) == "audio" else config.TELEGRAM_VIDEO_URL
                    await _send_now_playing(photo, [config.SUPPORT_CHAT, title[:23], check[0]["dur"], user], "tg")
                elif videoid == "soundcloud":
                    await _send_now_playing(
                        config.SOUNCLOUD_IMG_URL,
                        [config.SUPPORT_CHAT, title[:23], check[0]["dur"], user],
                        "tg",
                    )
                else:
                    img = await get_thumb(videoid)
                    await _send_now_playing(
                        img,
                        [f"https://t.me/{nand.username}?start=info_{videoid}", title[:23], check[0]["dur"], user],
                    )

    async def ping(self):
        pings = []
        strings = [config.STRING1, config.STRING2, config.STRING3, config.STRING4, config.STRING5]
        for string, client in zip(strings, self._clients):
            if string:
                try:
                    pings.append(await client.ping)
                except:
                    pass
        if not pings:
            return "0"
        return str(round(sum(pings) / len(pings), 3))

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Client...\n")
        strings = [config.STRING1, config.STRING2, config.STRING3, config.STRING4, config.STRING5]
        for string, client in zip(strings, self._clients):
            if string:
                await client.start()

    async def decorators(self):
        clients = self._clients

        for c in clients:
            @c.on_update()
            async def stream_services_handler(client, update):
                try:
                    from pytgcalls.types import ChatUpdate
                    if isinstance(update, ChatUpdate):
                        if update.status in (
                            ChatUpdate.Status.KICKED,
                            ChatUpdate.Status.LEFT_CALL,
                            ChatUpdate.Status.CLOSED_VOICE_CHAT,
                        ):
                            await self.stop_stream(update.chat_id)
                except Exception:
                    pass

        for c in clients:
            @c.on_update()
            async def stream_end_handler(client, update):
                try:
                    if isinstance(update, StreamEnded):
                        await self.change_stream(client, update.chat_id)
                except Exception:
                    pass


AnglePriya = Call()
