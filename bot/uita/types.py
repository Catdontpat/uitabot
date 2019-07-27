"""Defines various container and running state types for the Discord API."""
import asyncio
import discord
from typing import Dict, List, Optional

import uita.audio
import uita.utils

import logging
log = logging.getLogger(__name__)


class DiscordState():
    """Container for active Discord data.

    Attributes
    ----------
    servers : dict(uita.types.DiscordServer)
        Dict of servers bot is connected to indexed by server ID.
    voice_connections : dict(uita.types.DiscordVoiceClient)
        Dict of voice channels bot is connected to indexed by server ID.

    """
    def __init__(self) -> None:
        self.servers: Dict[str, DiscordServer] = {}
        self.voice_connections: Dict[str, DiscordVoiceClient] = {}

    def __str__(self) -> str:
        dump_str = "DiscordState() {}:\n".format(hash(self))
        for key, server in self.servers.items():
            dump_str += "server {}: {}\n".format(server.id, server.name)
            for key, channel in server.channels.items():
                dump_str += "\tchannel {}: {}\n".format(channel.id, channel.name)
            for user_id, user_name in server.users.items():
                dump_str += "\tuser {}: {}\n".format(user_id, user_name)
        return dump_str

    def initialize_from_bot(self, bot: discord.Client) -> None:
        """Initialize Discord state from a `discord.Client`

        Parameters
        ----------
        bot : discord.Client
            Bot containing initial Discord state to copy.

        """
        log.info("Bot state synced to Discord")
        for server in bot.guilds:
            discord_channels = {
                str(channel.id): DiscordChannel(
                    str(channel.id),
                    channel.name,
                    channel.type,
                    str(channel.category_id) if channel.category_id else None,
                    channel.position
                )
                for channel in server.channels
                if uita.utils.verify_channel_visibility(channel, server.me)
            }
            role = uita.server.database.get_server_role(str(server.id))
            discord_users = {
                str(user.id):
                user.name for user in server.members
                if uita.utils.verify_user_permissions(user, role)
            }
            self.servers[str(server.id)] = DiscordServer(
                str(server.id),
                server.name,
                discord_channels,
                discord_users,
                server.icon
            )
            self.voice_connections[str(server.id)] = DiscordVoiceClient(str(server.id), bot.loop)

    def channel_add(self, channel: "DiscordChannel", server_id: str) -> None:
        """Add a server channel to Discord state.

        Parameters
        ----------
        channel : uita.types.DiscordChannel
            Channel to be added to server.
        server_id : str
            ID of server that channel belongs to.

        """
        log.debug("channel_add {}".format(channel.id))
        self.servers[server_id].channels[channel.id] = channel

    def channel_remove(self, channel_id: str, server_id: str) -> None:
        """Remove a server channel from Discord state.

        Parameters
        ----------
        channel_id : str
            ID of channel to be removed from server.
        server_id : str
            ID of server that channel belongs to.

        """
        log.debug("channel_remove {}".format(channel_id))
        del self.servers[server_id].channels[channel_id]

    def server_add(self, server: "DiscordServer", bot: discord.Client) -> None:
        """Add an accessible server to Discord state.

        Parameters
        ----------
        server : uita.types.DiscordServer
            Server that bot has joined.
        bot : discord.Client
            Bot that handles voice client connections.

        """
        log.debug("server_add {}".format(server.id))
        self.servers[server.id] = server
        # Non-POD type with persistent connections, doesn't need to be updated
        if server.id not in self.voice_connections:
            self.voice_connections[server.id] = DiscordVoiceClient(server.id, bot.loop)

    def server_remove(self, server_id: str) -> None:
        """Remove an accessible server from Discord state.

        Parameters
        ----------
        server_id : str
            ID of server that bot has left.

        """
        log.debug("server_remove {}".format(server_id))
        del self.servers[server_id]
        del self.voice_connections[server_id]

    def server_add_user(self, server_id: str, user_id: str, user_name: str) -> None:
        """Add an accessible server for a user.

        Parameters
        ----------
        server_id : str
            Server that can be accessed.
        user_id : str
            User to update.
        user_name : str
            New username.

        """
        self.servers[server_id].users[user_id] = user_name

    def server_remove_user(self, server_id: str, user_id: str) -> None:
        """Remove an inaccessible server for a user.

        Parameters
        ----------
        server_id : str
            Server that can no longer be accessed.
        user_id : str
            User to update.

        """
        del self.servers[server_id].users[user_id]

    def server_get_role(self, server_id: str) -> Optional[str]:
        """Get the role required to use bot commands.

        Parameters
        ----------
        server_id : str
            Server that can no longer be accessed.

        Returns
        -------
        str
            ID of required role. Can be `None` for no requirement.

        """
        try:
            return self.servers[server_id].role
        except KeyError:
            pass
        # Get database value if server is not stored in state yet (like in on_guild_join)
        return uita.server.database.get_server_role(server_id)

    def server_set_role(self, server_id: str, role_id: Optional[str]) -> None:
        """Set a role required to use bot commands. `None` for free access.

        Parameters
        ----------
        server_id : str
            Server that can no longer be accessed.
        role_id : str
            ID of required role. Can be `None` for no requirement.

        """
        uita.server.database.set_server_role(server_id, role_id)
        try:
            self.servers[server_id].role = role_id
        except KeyError:
            pass


class DiscordChannel():
    """Container for Discord channel data.

    Parameters
    ----------
    id : str
        Unique channel ID.
    name : str
        Channel name.
    type : discord.ChannelType
        Channel type.
    position : int
        Ordered position in channel list.

    Attributes
    ----------
    id : str
        Unique channel ID.
    name : str
        Channel name.
    type : discord.ChannelType
        Channel type.
    category : str
        Unique category channel ID. `None` if not a categorized subchannel.
    position : int
        Ordered position in channel list.

    """
    def __init__(
        self,
        id: str,
        name: str,
        type: discord.ChannelType,
        category: Optional[str],
        position: int
    ) -> None:
        self.id = id
        self.name = name
        self.type = type
        self.category = category
        self.position = position


class DiscordServer():
    """Container for Discord server data.

    Parameters
    ----------
    id : str
        Unique server ID.
    name : str
        Server name.
    channels : dict(channel_id: uita.types.DiscordChannel)
        Dictionary of channels in server.
    users : dict(user_id: user_name)
        Dictionary of users in server with access to bot commands.
    icon : str
        Server icon hash.

    Attributes
    ----------
    id : str
        Unique server ID.
    name : str
        Server name.
    channels : dict(channel_id: uita.types.DiscordChannel)
        Dictionary of channels in server.
    users : dict(user_id: user_name)
        Dictionary of users in server with access to bot commands.
    icon : str
        Server icon hash. `None` if no custom icon exists.
    role : str
        Role ID needed to use bot commands. Set to `None` for unrestricted access.

    """
    def __init__(
        self, id: str,
        name: str,
        channels: Dict[str, DiscordChannel],
        users: Dict[str, str],
        icon: Optional[str]
    ) -> None:
        self.id = id
        self.name = name
        self.channels = channels
        self.users = users
        self.icon = icon
        self.role: Optional[str] = uita.server.database.get_server_role(self.id)


class DiscordUser():
    """Container for Discord user data.

    Parameters
    ----------
    id : str
        Unique user ID.
    name : str
        User name.
    avatar : str
        URL to user avatar.
    active_server_id : str
        Discord server that user has joined. None if user has not joined a server yet.

    Attributes
    ----------
    id : str
        Unique user ID.
    name : str
        User name.
    avatar : str
        URL to user avatar.
    active_server_id : str
        Discord server that user has joined. `None` if user has not joined a server yet.

    """
    def __init__(
        self,
        id: str,
        name: str,
        avatar: str,
        active_server_id: Optional[str]
    ) -> None:
        self.id = id
        self.name = name
        # Hack for discord.py forcing WebP extensions even though it has terrible browser support
        # This also replaces animated GIFs with static PNGs, but thats for the best
        self.avatar = avatar.rpartition(".")[0] + ".png"
        self.active_server_id = active_server_id


class DiscordVoiceClient():
    """Container for Discord voice connections.

    Parameters
    ----------
    server_id : str
        Server ID to connect to.
    loop : asyncio.AbstractEventLoop, optional
        Event loop for audio tasks to run in.

    Attributes
    ----------
    server_id : str
        Server ID to connect to.
    loop : asyncio.AbstractEventLoop
        Event loop for audio tasks to run in.

    """
    def __init__(self, server_id: str, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self.server_id = server_id
        self.loop = loop or asyncio.get_event_loop()

        async def on_queue_change(
            queue: List[uita.audio.Track],
            user: Optional[DiscordUser] = None
        ) -> None:
            # If the queue is changed and the bot is not connected to a voice channel, find the
            # voice channel of the user who most recently changed the queue and join it.
            # User is None for queue change callbacks that should not cause the bot to join a
            # channel, such as queue re-ordering and removal
            if self._voice is None and user is not None and len(queue) > 0:
                discord_server = uita.bot.get_guild(int(self.server_id))
                discord_user = discord_server.get_member(int(user.id)) if discord_server else None
                if discord_user is not None and discord_user.voice is not None:
                    channel = discord_user.voice.channel
                    if channel is not None:
                        await self.connect(str(channel.id))
            elif len(queue) == 0:
                await self.disconnect()
            message = uita.message.PlayQueueSendMessage(queue)
            uita.server.send_all(message, self.server_id)

        def on_status_change(status: uita.audio.Status) -> None:
            message = uita.message.PlayStatusSendMessage(status)
            uita.server.send_all(message, self.server_id)

        self._playlist = uita.audio.Queue(
            maxlen=100,
            on_queue_change=on_queue_change,
            on_status_change=on_status_change,
            loop=self.loop
        )

        self._voice: Optional[discord.VoiceClient] = None
        self._voice_lock = asyncio.Lock(loop=self.loop)

    @property
    def active_channel(self) -> Optional[DiscordChannel]:
        if self._voice is not None and self._voice.is_connected():
            channel = self._voice.channel
            return DiscordChannel(
                str(channel.id),
                channel.name,
                channel.type,
                str(channel.category_id),
                channel.position
            )
        return None

    async def connect(self, channel_id: str) -> None:
        """Connect bot to a voice a voice channel in this server.

        Parameters
        ----------
        channel_id : str
            ID of channel to connect to.

        """
        server = uita.bot.get_guild(int(self.server_id))
        channel = server.get_channel(int(channel_id)) if server else None
        if (
            channel is None or
            not isinstance(channel, discord.VoiceChannel) or
            not uita.utils.verify_channel_visibility(channel, channel.guild.me)
        ):
            raise uita.exceptions.MalformedMessage("Tried to join invalid channel")

        with await self._voice_lock:
            if self._voice is None:
                try:
                    self._voice = await channel.connect(timeout=5)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    log.warning("Failed to join channel {}({})".format(channel.name, channel.id))
                    return
                await self._playlist.play(self._voice)
            else:
                await self._voice.move_to(channel)

    async def disconnect(self) -> None:
        """Disconnect bot from the voice channels in this server."""
        with await self._voice_lock:
            if self._voice is not None:
                await self._playlist.stop()
                try:
                    await self._voice.disconnect()
                except asyncio.CancelledError:
                    log.warning("Failed to disconnect from channel")
                self._voice = None

    async def enqueue_file(self, path: str, user: DiscordUser) -> None:
        """Queues a file to be played by the running playlist task.

        Parameters
        ----------
        path : str
            Path to audio resource to be played.
        user : uita.types.DiscordUser
            User that requested track.

        Raises
        ------
        uita.exceptions.ClientError
            If called with an unusable audio URL.

        """
        await self._playlist.enqueue_file(path, user)

    async def enqueue_url(self, url: str, user: DiscordUser) -> None:
        """Queues a URL to be played by the running playlist task.

        Parameters
        ----------
        url : str
            URL for audio resource to be played.
        user : uita.types.DiscordUser
            User that requested track.

        Raises
        ------
        uita.exceptions.ClientError
            If called with an unusable audio URL.

        """
        await self._playlist.enqueue_url(url, user)

    def queue(self) -> List[uita.audio.Track]:
        """Retrieves a list of currently queued audio resources for this connection.

        Returns
        -------
        list
            Ordered list of audio resources queued for playback.

        """
        return self._playlist.queue()

    def queue_full(self) -> bool:
        """Tests if the queue is at capacity.

        Returns
        -------
        bool
            True if the queue is full.

        """
        return self._playlist.queue_full()

    def status(self) -> uita.audio.Status:
        """Returns the current playback status.

        Returns
        -------
        uita.audio.Status
            Enum of current playback status (playing, paused, etc).

        """
        return self._playlist.status

    async def move(self, track_id: str, position: int) -> None:
        """Moves a track to a new position in the playback queue.

        Parameters
        ----------
        track_id : str
            Track ID of audio resource to be moved.
        position : int
            Index position for the track to be moved to.

        """
        await self._playlist.move(track_id, position)

    async def remove(self, track_id: str) -> None:
        """Removes a track from the playback queue.

        Parameters
        ----------
        track_id : str
            Track ID of audio resource to be removed.

        """
        await self._playlist.remove(track_id)
