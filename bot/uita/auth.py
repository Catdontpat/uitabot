"""Authenticates Discord users."""

import asyncio
from typing import NamedTuple, Optional

import uita.discord_api
import uita.exceptions
import uita.types


class Session(NamedTuple):
    """Contains session authentication data.

    Parameters
    ----------
    handle : str
        Session handle.
    secret : str
        Session secret.

    Attributes
    ----------
    handle : str
        Session handle.
    secret : str
        Session secret.

    """
    handle: str
    secret: str


async def verify_session(
    session: Session,
    database: "uita.database.Database",
    config: uita.config.Config,
    loop: Optional[asyncio.AbstractEventLoop] = None
) -> uita.types.DiscordUser:
    """Authenticates a user session against sessions database and Discord API.

    Parameters
    ----------
    session : uita.auth.Session
        Session to compare against database.
    database : uita.database.Database
        Database containing valid sessions.
    config : uita.config.Config
        Configuration options containing API keys.
    loop : asyncio.AbstractEventLoop, optional
        Event loop to attach blocking request threads to.

    Returns
    -------
    uita.types.DiscordUser
        User object of authenticated user.

    Raises
    ------
    uita.exceptions.AuthenticationError
        If authentication fails.

    """
    loop = loop or asyncio.get_event_loop()
    token = database.get_access_token(session)
    if token is not None:
        try:
            user = await uita.discord_api.get("/users/@me", token, loop)
            return uita.types.DiscordUser(
                id=user["id"],
                name=user["username"],
                avatar=uita.discord_api.avatar_url(user),
                active_server_id=None
            )
        except uita.exceptions.AuthenticationError:
            database.delete_session(session)
    raise uita.exceptions.AuthenticationError("Session authentication failed")


async def verify_code(
    code: str,
    database: "uita.database.Database",
    config: uita.config.Config,
    loop: Optional[asyncio.AbstractEventLoop] = None
) -> Session:
    """Authenticates a user by passing an access code to the Discord API in exchange for a token.

    On success, creates and stores a session in the local database.

    Parameters
    ----------
    code : str
        Access code to authenticate.
    database : uita.database.Database
        Database containing valid sessions.
    config : uita.config.Config
        Configuration options containing API keys.
    loop : asyncio.AbstractEventLoop, optional
        Event loop to attach blocking request threads to.

    Returns
    -------
    uita.auth.Session
        Session object for authenticated user.

    Raises
    ------
    uita.exceptions.AuthenticationError
        If authentication fails.

    """
    loop = loop or asyncio.get_event_loop()
    api_data = await uita.discord_api.auth(code, config, loop)
    return database.add_session(
        api_data["access_token"],
        api_data["expires_in"]
    )
