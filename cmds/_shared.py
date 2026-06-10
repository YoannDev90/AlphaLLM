"""Shared helpers for command handlers.

Utility helpers for formatting interaction context and logging command
lifecycle events (start, end, error), plus helpers for deferring and
sending interaction responses.
"""

import time
from typing import Any, Optional


def interaction_context(interaction: Any) -> str:
    """Build a short textual context string for an interaction.

    Parameters
    ----------
    interaction : Any
        Discord interaction object.

    Returns
    -------
    str
        Human-readable context including user, guild and channel.
    """
    guild_name = interaction.guild.name if interaction.guild is not None else "DM"
    channel_name = getattr(interaction.channel, "name", None)
    channel_id = getattr(interaction.channel, "id", None)
    if channel_name is None:
        channel_name = f"#{channel_id}" if channel_id is not None else "unknown"

    return (
        f"user={interaction.user} (id={interaction.user.id}), "
        f"guild={guild_name}, channel={channel_name}"
    )


def log_command_start(
    logger: Any, command_name: str, interaction: Any, **extra
) -> None:
    """Log the start of a command invocation.

    Parameters
    ----------
    logger : Any
        Logger instance to use for logging.
    command_name : str
        Name of the invoked command.
    interaction : Any
        The Discord interaction that triggered the command.
    **extra : dict
        Optional additional context to include in the log.
    """
    details = interaction_context(interaction)
    if extra:
        details = f"{details}, extra={extra}"
    logger.info("Command /%s invoked (%s)", command_name, details)


def log_command_end(
    logger: Any, command_name: str, start_time: float, status: str = "ok"
) -> None:
    """Log the end of a command and its duration.

    Parameters
    ----------
    logger : Any
        Logger instance to use for logging.
    command_name : str
        Name of the command that completed.
    start_time : float
        Perf-counter timestamp when the command started.
    status : str
        Optional status string to include in the log (default: "ok").
    """
    duration = time.perf_counter() - start_time
    logger.info("Command /%s completed in %.2fs (%s)", command_name, duration, status)


def log_command_error(logger: Any, command_name: str, exc: Exception) -> None:
    """Log an exception raised while handling a command.

    Parameters
    ----------
    logger : Any
        Logger instance to use for logging.
    command_name : str
        Name of the command where the error occurred.
    exc : Exception
        The exception instance caught.
    """
    logger.error("Error in /%s: %s", command_name, exc, exc_info=True)


async def defer_interaction(interaction: Any, *, ephemeral: bool = True) -> bool:
    """Defer an interaction response if it has not already been deferred.

    Parameters
    ----------
    interaction : Any
        Discord interaction object.
    ephemeral : bool
        Whether the deferred response (and eventual reply) should be
        ephemeral (default: True).

    Returns
    -------
    bool
        True if the call deferred the response, False if the response was
        already done.
    """
    if interaction.response.is_done():
        return False

    await interaction.response.defer(ephemeral=ephemeral)
    return True


async def send_interaction(
    interaction: Any,
    *,
    content: Optional[str] = None,
    embed: Any = None,
    embeds: Any = None,
    ephemeral: bool = True,
) -> Any:
    """Send a message in response to an interaction handling both response and followup.

    This helper avoids passing both `embed` and `embeds` to Discord (which
    is not allowed) and uses `interaction.response` when available, otherwise
    falls back to `interaction.followup`.

    Parameters
    ----------
    interaction : Any
        Discord interaction object.
    content : Optional[str]
        Optional content string for the message. (Default value = None)
    embed : Any
        Optional single embed. (Default value = None)
    embeds : Any
        Optional list of embeds. (Default value = None)
    ephemeral : bool
        Whether the reply should be ephemeral (default: True).

    Returns
    -------
    Any
        The message object returned by the Discord API.
    """
    kwargs = {}
    if content is not None:
        kwargs["content"] = content
    if embeds is not None:
        kwargs["embeds"] = embeds
    elif embed is not None:
        kwargs["embed"] = embed
    kwargs["ephemeral"] = ephemeral

    if interaction.response.is_done():
        return await interaction.followup.send(**kwargs)

    return await interaction.response.send_message(**kwargs)
