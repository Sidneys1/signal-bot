"""High-level interface definitions."""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from abc import abstractmethod
from datetime import datetime

from .args import SendMessageArgs
from .types import Account, GroupId, DataMessage
from .aliases import Context, MessageCb, CronCb, CronItem, AnyCb, RpcRet

########################
# High Level Protocols #
########################


@runtime_checkable
class PersonalityProto(Protocol):
    """
    Defines a "personality" that applies only to messages in specific contexts (e.g., in a specific group).

    This ``Protocol`` contains shared functionality between a :class:`SignalBot` instance (a "root" personality) and
    individual :class:`signal_bot.personality.Personality` instances. When a message is received, it is checked against
    any personalities' callbacks first, then the root peronality's callbacks.
    
    To use, create an instance of (or subclass) :class:`~signal_bot.personality.Personality` and register it with
    :func:`SignalBot.add_personality`.

    Not listed here are associated ``remove_xxx(...)`` methods (e.g.,
    :func:`~signal_bot.personality.Personality.remove_cron`).
    """

    def matches_context(self, context: Context) -> bool:
        """
        Whether this personality matches a given context.

        :param context: The context to match against.
        :type context: :data:`~signal_bot.aliases.Context`
        """

    def on_message(self, cb: MessageCb) -> None:
        """
        Register a callback to be called on any DataMessage.
        
        :param cb: The function to call.
        :type cb: :data:`~signal_bot.aliases.MessageCb`
        """

    def on_prefix(self, prefix: str, cb: MessageCb) -> None:
        """
        Register a callback to be called on any DataMessage matching a given prefix (exact match).
        
        :param prefix: The exact-match prefix to trigger on.
        :param cb: The function to call.
        :type cb: :data:`~signal_bot.aliases.MessageCb`
        """

    def on_cron(self, schedule: str, cb: CronCb) -> CronItem:
        """
        Register a callback to be called on a Cron schedule.
        
        :param schedule: The Cron schedule to trigger on.
        :param cb: The function to call.
        :type cb: :data:`~signal_bot.aliases.MessageCb`
        :rtype: :data:`~signal_bot.aliases.CronItem`
        """

    def on_mention(self, mention: Account, cb: MessageCb) -> None:
        """
        Register a callback to be called when a given Account is @-mentioned.

        :param mention: The Signal account to trigger on mentions of.
        :type mention: :data:`~signal_bot.types.Account`
        :param cb: The function to call.
        :type cb: :data:`~signal_bot.aliases.MessageCb`
        """

    def on_keyword(self, keyword: str, cb: MessageCb, case_sensitive=False, whole_word=True) -> None:
        """
        Register a callback to be called when DataMessage contains a keyword.

        :param keyword: The keyword to trigger on.
        :param cb: The function to call.
        :type cb: :data:`~signal_bot.aliases.MessageCb`
        :param case_sensitive: Whether the match is case-sensitive.
        :type case_sensitive: :data:`bool`
        :param whole_word: Whether to match whole words only.
        :type whole_word: :data:`bool`
        """

    async def started(self, signal: 'SignalBot') -> None:
        """
        Handle when ``SignalBot`` is first started.
        
        :param signal: An instance of the current ``SignalBot``.
        :type signal: :class:`~SignalBot`
        """

    @abstractmethod
    def handle_callback_exception(self, exception: BaseException, cb: AnyCb) -> bool:
        """
        Personalities should implement this to handle when unhandled exceptions occur in a callback.

        :param exception: The exception that occurred.
        :param cb: The callback that raised the exception.
        :type cb: :data:`~signal_bot.aliases.AnyCb`
        :returns: Whether Cron callbacks should be rescheduled.
        """


class SignalBot(PersonalityProto, Protocol):
    """
    The high-level abstraction of ``signal_bot`` functionality.

    Implementation can be found in ``signal_bot._signal_impl``.
    To create an instance, call :meth:`signal_bot.create`.
    """

    def __init__(self) -> None:  # noqa: D107
        # TODO: remove this limitation in future versions.
        raise TypeError("Instances must be created with `signal_bot.create(...)`.")

    @property
    def account(self) -> Account:
        """The currently registered Signal account."""

    async def send_reaction(self, to: DataMessage, emoji: str) -> RpcRet:
        """
        React to a previous message.

        :param to: The message to react to.
        :param emoji: The emoji to react with.
        """

    async def send_typing(self, to: Account | GroupId, stop=False) -> RpcRet:
        """
        Start (or stop) the "Typing..." indicator.

        When started, will display for 15 seconds unless stopped.

        :param to: The destination of the typing indicator (an individual or a group).
        :param stop: Stop (rather than start) the typing indicator.
        :type stop: :data:`bool`
        """

    async def send_message(self,
                           to: Account | GroupId,
                           message: str | None = None,
                           args: SendMessageArgs | None = None) -> RpcRet:
        """
        Send a message.

        :param to: The destination of the message (an individual or a group).
        :param message: The textual message to send (if any).
        :param args: Additional arguments to ``send_message``.
        """

    async def delete_message(self, to: Account | GroupId, target_timestamp: datetime) -> RpcRet:
        """
        Delete a sent message (by timestamp).

        :param to: The destination (an individual or a group) in which to delete a message.
        :param target_timestamp: The timestamp of the message to delete.
        """

    async def run(self) -> None:
        """
        Start Cron callbacks and the message pump loop.
        
        Runs until the transport raises ``asyncio.CancelledError`` (e.g., :meth:`stop` is called).
        """

    async def stop(self) -> None:
        """Stop the message pump loop (if running) and any scheduled Cron callbacks, in-flight requests, etc."""

    def add_personality(self, personality: PersonalityProto) -> None:
        """
        Add a sub-personality.
        
        :param personality: The :class:`~signal_bot.personality.Personality` to add.
        """
