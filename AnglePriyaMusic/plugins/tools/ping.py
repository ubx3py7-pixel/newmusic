from datetime import datetime

from pyrogram import filters
from pyrogram.types import Message

from AnglePriyaMusic import nand
from AnglePriyaMusic.core.call import AnglePriya
from AnglePriyaMusic.utils import bot_sys_stats
from AnglePriyaMusic.utils.decorators.language import language
from AnglePriyaMusic.utils.inline import supp_markup
from config import BANNED_USERS, PING_IMG_URL


@nand.on_message(filters.command(["ping", "alive"]) & ~BANNED_USERS)
@language
async def ping_com(client, message: Message, _):
    start = datetime.now()
    response = await message.reply_photo(
        photo=PING_IMG_URL,
        caption=_["ping_1"].format(nand.mention),
    )
    pytgping = await AnglePriya.ping()
    UP, CPU, RAM, DISK = await bot_sys_stats()
    resp = (datetime.now() - start).microseconds / 1000
    await response.edit_text(
        _["ping_2"].format(resp, nand.mention, UP, RAM, CPU, DISK, pytgping),
        reply_markup=supp_markup(_),
    )
