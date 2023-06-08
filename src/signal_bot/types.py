from __future__ import annotations

from asyncio import Future
from typing import Literal, TypedDict, NotRequired, Required, Any, NewType
from datetime import datetime, timedelta

from ._util import to_lower_camel_case


Account = NewType('Account', str)
GroupId = NewType('GroupId', str)


class NotificationFrame(TypedDict):
    jsonrpc: Literal["2.0"]
    method: str
    params: Any
    id: NotRequired[str | int | None]


class ErrorFrame(TypedDict):
    code: int
    message: str
    data: NotRequired[Any]


class ResponseFrame(TypedDict):
    jsonrpc: Literal["2.0"]
    error: NotRequired[ErrorFrame]
    result: NotRequired[Any]
    id: str | int | None

class Response:
    result: Any
    def __init__(self, frame: ResponseFrame):
        self.result = frame.get('result', None)

    @classmethod
    async def from_future_frame(cls, frame: Future[ResponseFrame]):
        return cls(await frame)


class GroupInfoFrame(TypedDict):
    groupId: str
    type: Literal['UPDATE', 'DELIVER']


class DataMessageFrame(TypedDict, total=False):
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

TypingMessage = dict

class EnvelopeFrame(TypedDict):
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
    timestamp: datetime
    unix_timestamp: int
    sender: Account
    sender_name: str
    expires_in: timedelta

    message: str|None = None
    view_once: bool|None = None
    reaction: Any|None = None
    quote: Any|None = None
    payment: Any|None = None
    mentions: list[Any]|None = None
    previews: list[Any]|None = None
    attachments: list[Any]|None = None
    sticker: Any|None = None
    remote_delete: Any|None = None
    contacts: list[Any]|None = None
    text_styles: list[Any]|None = None
    group_info: GroupInfoFrame|None = None
    story_context: Any|None = None

    def __init__(self, frame: EnvelopeFrame):
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
