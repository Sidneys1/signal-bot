"""Common types for signal_bot."""

from __future__ import annotations  

from asyncio import Future
from typing import Literal, TypedDict, NotRequired, Required, Any, NewType
from datetime import datetime, timedelta

from ._util import to_lower_camel_case


Account = NewType('Account', str)
GroupId = NewType('GroupId', str)


class NotificationFrame(TypedDict):
    """Raw JSON-RPC notification frame (type hint only, will be raw `dict`)."""

    jsonrpc: Literal["2.0"]
    method: str
    params: Any
    id: NotRequired[str | int | None]


class ErrorFrame(TypedDict):
    """Raw JSON-RPC error frame (type hint only, will be raw `dict` at runtime)."""

    code: int
    message: str
    data: NotRequired[Any]


class ResponseFrame(TypedDict):
    """Raw JSON-RPC response frame (type hint only, will be raw `dict` at runtime)."""

    jsonrpc: Literal["2.0"]
    error: NotRequired[ErrorFrame]
    result: NotRequired[Any]
    id: str | int | None

class Response:
    """Realized JSON-RPC response."""

    __slots__ = ['result']
    result: Any
    
    def __init__(self, frame: ResponseFrame):
        """Create a `Response` from a `ResponseFrame`."""
        self.result = frame.get('result', None)

    @classmethod
    async def from_future_frame(cls, frame: Future[ResponseFrame]):
        """Create a future `Response` from a future `ResponseFrame`."""
        return cls(await frame)


class GroupInfoFrame(TypedDict):
    """Raw signal-cli GroupInfo frame (type hint only, will be raw `dict` at runtime)."""

    groupId: str
    type: Literal['UPDATE', 'DELIVER']


class DataMessageFrame(TypedDict, total=False):
    """Raw signal-cli DataMessage frame (type hint only, will be raw `dict` at runtime)."""

    timestamp: Required[int]
    message: Required[str|None]
    expiresInSeconds: Required[int]
    viewOnce: bool
    reaction: Any
    quote: Any
    payment: Any
    mentions: list[Any]
    previews: list[Any]
    attachments: list[Any]
    sticker: Any
    remoteDelete: Any
    contacts: list[Any]
    textStyles: list[Any]
    groupInfo: GroupInfoFrame
    storyContext: Any

TypingMessage = dict  # TODO

class EnvelopeFrame(TypedDict):
    """Raw signal-cli Envelope frame (type hint only, will be raw `dict` at runtime)."""

    source: str
    sourceNumber: str
    sourceUuid: str
    sourceName: str
    sourceDevice: int
    timestamp: int
    dataMessage: NotRequired[DataMessageFrame]
    editMessage: NotRequired[Any]
    storymessage: NotRequired[Any]
    syncMessage: NotRequired[Any]
    callMessage: NotRequired[Any]
    receiptMessage: NotRequired[Any]
    typingMessage: NotRequired[TypingMessage]


class DataMessage:
    """A realized DataMessage."""

    __slots__ = ("timestamp", "unix_timestamp", "sender", "sender_name", "expires_in", "message", "view_once",
                 "reaction", "quote", "payment", "mentions", "previews", "attachments", "sticker", "remote_delete",
                 "contacts", "text_styles", "group_info", "story_context")
    timestamp: datetime
    unix_timestamp: int
    sender: Account
    sender_name: str
    expires_in: timedelta

    message: str|None
    view_once: bool|None
    reaction: Any|None
    quote: Any|None
    payment: Any|None
    mentions: list[Any]|None
    previews: list[Any]|None
    attachments: list[Any]|None
    sticker: Any|None
    remote_delete: Any|None
    contacts: list[Any]|None
    text_styles: list[Any]|None
    group_info: GroupInfoFrame|None
    story_context: Any|None

    def __init__(self, frame: EnvelopeFrame):
        """Create a `DataMessage` from an `EnvelopeFrame`."""
        assert('dataMessage' in frame)
        self.timestamp = datetime.fromtimestamp(frame['dataMessage']['timestamp'] / 1000.0)
        self.unix_timestamp = frame['dataMessage']['timestamp']
        self.sender = Account(frame['sourceNumber'])
        self.sender_name = frame['sourceName']
        self.expires_in = timedelta(seconds=frame['dataMessage']['expiresInSeconds'])
        for name in self.__annotations__:
            if name.startswith('_') or getattr(self, name, None) is not None or name in ('timestamp', 'unix_timestamp', 'sender', 'sender_name', 'expires_in'):
                continue
            setattr(self, name, frame['dataMessage'].get(to_lower_camel_case(name), None))
