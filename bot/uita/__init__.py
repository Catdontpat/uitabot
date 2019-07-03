"""Music bot for Discord that can be controlled via websockets"""

__version__ = "0.2.0"
__author__ = "Dominic Bowden"
__copyright__ = "2018, Dominic Bowden"
__license__ = "ISC"

from discord import Client
from uita.ui_server import Server
from uita.types import DiscordState
import asyncio

# Use a bunch of globals because of decorator class methods
loop = asyncio.get_event_loop()
bot = Client(loop=loop)
server = Server()
state = DiscordState()

# Initialize bot and server decorators
import uita.bot_events, uita.server_events  # noqa: E401,E402,F401
