import asyncio
import importlib

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from AnglePriyaMusic import LOGGER, nand, userbot
from AnglePriyaMusic.core.call import AnglePriya
from AnglePriyaMusic.misc import sudo
from AnglePriyaMusic.plugins import ALL_MODULES
from AnglePriyaMusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS


async def init():
    if not any([config.STRING1, config.STRING2, config.STRING3, config.STRING4, config.STRING5]):
        LOGGER(__name__).error("Assistant client variables not defined, exiting...")
        exit()
    await sudo()
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except:
        pass
    await nand.start()
    for all_module in ALL_MODULES:
        importlib.import_module("AnglePriyaMusic.plugins" + all_module)
    LOGGER("AnglePriyaMusic.plugins").info("Successfully Imported Modules...")
    await userbot.start()
    await AnglePriya.start()
    try:
        await AnglePriya.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
    except NoActiveGroupCall:
        LOGGER("AnglePriyaMusic").error(
            "Please turn on the videochat of your log group/channel.\n\nStopping Bot..."
        )
        exit()
    except:
        pass
    await AnglePriya.decorators()
    LOGGER("AnglePriyaMusic").info(
        "Angle Priya Music Bot Started Successfully.\n\nDon't forget to visit @AnglePriyaBots"
    )
    await idle()
    await nand.stop()
    await userbot.stop()
    LOGGER("AnglePriyaMusic").info("Stopping AnglePriyaMusic Music Bot...")


if __name__ == "__main__":
    asyncio.run(init())
