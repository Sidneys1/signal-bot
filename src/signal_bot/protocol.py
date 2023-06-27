"""signal_bot high-level interface definitions."""

from typing import Protocol, Tuple, Callable, Awaitable, runtime_checkable
from asyncio import Future
from abc import abstractmethod

from .types import *
from .args import *


#######################
# Common Type Aliases #
#######################


RpcRet = Future[Response]  # Future values returned from JSON-RPC operations.

Name = str  # An individual Signal account's display name.
GroupContext = Tuple[Literal['group'], GroupId]
IndividualContext = Tuple[Literal['individual'], Account, Name]
Context = GroupContext|IndividualContext  # Used to identify the context in which a message was received.
                                          # Either ("group", "<group-id>"),
                                          # or ("individual", "<signal-account>", "<display-name>")

MessageCb = Callable[['SignalBot', Context, 'DataMessage'], Awaitable[bool]]  # Signature for personality callbacks.
CronCb = Callable[['SignalBot'], Awaitable[None]]  # Signature for personality Cron callbacks.
CronItem = Tuple[str, CronCb]  # A cron item definition. Used for `Personality.remove_cron(...)` or to identify the
                               # callback that triggered an exception in `Personality.handle_callback_exception`.

MessageHookDef = Tuple[Literal['message'], MessageCb]
PrefixHookDef = Tuple[Literal['prefix'], str, MessageCb]
KeywordHookDef = Tuple[Literal['keyword'], Tuple[str, bool], MessageCb]
MentionHookDef = Tuple[Literal['account'], Account, MessageCb]
CronHookDef = Tuple[Literal['cron'], str, CronCb]
AnyCb = MessageHookDef|PrefixHookDef|KeywordHookDef|MentionHookDef|CronHookDef


########################
# High Level Protocols #
########################


@runtime_checkable
class PersonalityProto(Protocol):
    """
    Defines a "personality" that applies certain callbacks to messages in certain contexts (e.g., in a specific group).

    This Protocol contains shared functionality between a Signal instance (a "root" personality) and individual
    personalities. When a message is received, it is checked against any `Personality`s' callbacks first, then the root
    `SignalBot`'s callbacks
    
    To use, create an instance of or subclass `signal_bot.personality.Personality` and register it with
    `SignalBot.add_personality(...)`.

    Not listed here are associated `remove_xxx(...)` methods (e.g., `remove_cron(...)`).
    """

    def matches_context(self, context: Context) -> bool:
        """Whether this personality matches a given context."""

    def on_message(self, cb: MessageCb) -> None:
        """Register a callback to be called on any DataMessage."""
    def on_prefix(self, prefix: str, cb: MessageCb) -> None:
        """Register a callback to be called on any DataMessage matching a given prefix (exact match)."""
    def on_cron(self, schedule: str, cb: CronCb) -> CronItem:
        """Register a callback to be called on a Cron schedule."""
    def on_mention(self, mention: Account, cb: MessageCb) -> None:
        """Register a callback to be called when a given Account is @-mentioned."""
    def on_keyword(self, keyword: str, cb: MessageCb, case_sensitive = False, whole_word = True) -> None:
        """Register a callback to be called when DataMessage contains a keyword."""

    @abstractmethod
    def handle_callback_exception(self, exception: BaseException, cb: AnyCb) -> bool:
        """
        Personalities should implement this to handle when unhandled exceptions occur in a callback.

        :returns: whether Cron callbacks should be rescheduled.
        """


class SignalBot(PersonalityProto, Protocol):
    """
    The high-level abstraction of signal_bot functionality.

    Implementation can be found in `signal_bot._signal_impl`. To create an instance, call `signal_bot.create(...)`.
    """

    def __init__(self) -> None:  # noqa: D107
        # TODO: remove this limitation in future versions.
        raise TypeError("Instances must be created with `signal_bot.create(...)`.")

    @property
    def account(self) -> Account:
        """The currently registered Signal account."""

    async def send_reaction(self, to: DataMessage, emoji: str) -> RpcRet:
        """React to a previous message."""
    async def send_typing(self, to: Account|GroupId, stop=False) -> RpcRet:
        """Start (or stop) the "Typing..." indicator."""
    async def send_message(self, to: Account|GroupId, message: str|None = None, args: SendMessageArgs|None = None) -> RpcRet:
        """Send a message."""
    async def delete_message(self, to: Account|GroupId, target_timestamp: datetime) -> RpcRet:
        """Delete a sent message (by timestamp)."""

    async def run(self) -> None:
        """
        Start Cron callbacks and the message pump loop.
        
        Runs until the transport raises `asyncio.CancelledError` (e.g., `SignalBot.stop()` is called).
        """
    async def stop(self) -> None:
        """Stop the message pump loop (if running) and any scheduled Cron callbacks, in-flight requests, etc."""

    def add_personality(self, personality: PersonalityProto) -> None:
        """Add a sub-personality."""
