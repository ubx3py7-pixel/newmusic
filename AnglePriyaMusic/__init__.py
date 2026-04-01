from AnglePriyaMusic.core.bot import AnglePriya
from AnglePriyaMusic.core.dir import dirr
from AnglePriyaMusic.core.git import git
from AnglePriyaMusic.core.userbot import Userbot
from AnglePriyaMusic.misc import dbb, heroku

from .logging import LOGGER

dirr()
git()
dbb()
heroku()

nand = AnglePriya()
userbot = Userbot()


from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
