from typing import Protocol, Sequence, Tuple, Callable, Awaitable, runtime_checkable, Type, Self, Dict, Iterable
from asyncio import Future
from abc import abstractmethod
from functools import partialmethod, wraps
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import ParseResult

from .types import *
from .args import *

RpcRet = Future[Response]
Name = str
GroupContext = Tuple[Literal['group'], GroupId]
IndividualContext = Tuple[Literal['individual'], Account, Name]
Context = GroupContext|IndividualContext

MessageCb = Callable[['Signal', Context, 'DataMessage'], Awaitable[bool]]
CronCb = Callable[['Signal'], Awaitable[None]]
CronItem = Tuple[str, CronCb]

MessageHookDef = Tuple[Literal['message'], MessageCb]
PrefixHookDef = Tuple[Literal['prefix'], str, MessageCb]
KeywordHookDef = Tuple[Literal['keyword'], Tuple[str, bool], MessageCb]
MentionHookDef = Tuple[Literal['account'], Account, MessageCb]
CronHookDef = Tuple[Literal['cron'], str, CronCb]
AnyCb = MessageHookDef|PrefixHookDef|KeywordHookDef|MentionHookDef|CronHookDef


class JsonRpcHandler(Protocol):
    """Signal instance which `JsonRpcTransport` uses to handle incoming JSON RPC responses and notifications."""
    async def handle_notification(self, notification: NotificationFrame) -> None: ...
    async def handle_response(self, response: ResponseFrame) -> None: ...


class JsonRpcTransport(Protocol):
    """Allows for communication with signal-cli."""
    PROTOS: Dict[str, Type[Self]] = {}

    @classmethod
    async def create(self, connection: ParseResult) -> None: ...

    def __init_subclass__(cls, /, scheme: str|Iterable[str], *args, **kwargs) -> None:
        if isinstance(scheme, str):
            JsonRpcTransport.PROTOS[scheme] = cls
        else:
            JsonRpcTransport.PROTOS.update({x: cls for x in scheme})
        return super().__init_subclass__(*args, **kwargs)

    async def write(self, data: NotificationFrame, handler: JsonRpcHandler) -> None: ...
    async def listen(self, handler: JsonRpcHandler) -> None: ...

    async def terminate(self) -> None: ...


class SignalRpc(Protocol):
    async def send_reaction(self, to: DataMessage, emoji: str) -> RpcRet: ...
    async def send_typing(self, to: Account|GroupId, stop=False) -> RpcRet: ...
    stop_typing = partialmethod(send_typing, stop=True)
    async def send_message(self, to: Account|GroupId, message: str|None = None, args: SendMessageArgs|None = None) -> RpcRet: ...
    async def delete_message(self, to: Account|GroupId, target_timestamp: datetime) -> RpcRet: ...


@runtime_checkable
class PersonalityProto(Protocol):
    def __init__(self, contexts: Sequence[Account | GroupId] = tuple()): ...
    def matches_context(self, context: Context) -> bool: ...

    def start_crons(self, signal: 'Signal') -> None: ...
    def stop_crons(self) -> None: ...
    
    def on_message(self, cb: MessageCb) -> None: ...
    def on_prefix(self, prefix: str, cb: MessageCb) -> None: ...
    def on_cron(self, schedule: str, cb: CronCb) -> CronItem: ...
    def on_mention(self, mention: Account, cb: MessageCb) -> None: ...
    def on_keyword(self, keyword: str, cb: MessageCb, case_sensitive = False, whole_word = True) -> None: ...

    @abstractmethod
    def handle_callback_exception(self, exception: BaseException, cb: AnyCb) -> bool: ...


class RootPersonality(PersonalityProto, Protocol):
    def add_personality(self, personality: PersonalityProto) -> None: ...


class Signal(SignalRpc, RootPersonality, JsonRpcHandler, Protocol):
    @property
    def account(self) -> Account: ...

    async def run(self) -> None: ...
    async def stop(self) -> None: ...
