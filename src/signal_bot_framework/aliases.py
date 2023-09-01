"""Common type aliases."""

from __future__ import annotations

from typing import TypeAlias, Tuple, Literal, Callable, Awaitable, TYPE_CHECKING
from asyncio import Future

from .types import Response, GroupId, Account, DataMessage

RpcRet: TypeAlias = Future[Response]
"""Future values returned from JSON-RPC operations."""

Name: TypeAlias = str
"""An individual Signal account's display name."""

GroupContext: TypeAlias = Tuple[Literal['group'], GroupId]
IndividualContext: TypeAlias = Tuple[Literal['individual'], Account, Name]
Context: TypeAlias = GroupContext | IndividualContext
"""
Used to identify the context in which a message was received.

Either ("group", "<group-id>"), or ("individual", "<signal-account>", "<display-name>")
"""

MessageCb: TypeAlias = Callable[['SignalBot', Context, DataMessage], Awaitable[bool]]
"""Signature for personality callbacks."""

CronCb: TypeAlias = Callable[['SignalBot'], Awaitable[None]]
"""Signature for personality Cron callbacks."""

CronItem: TypeAlias = Tuple[str, CronCb]
"""
A cron item definition.

Used for :meth:`~signal_bot_framework.personality.Personality.remove_cron` or to identify the callback that triggered an
exception in :meth:`~signal_bot_framework.personality.Personality.handle_callback_exception`.
"""

MessageHookDef: TypeAlias = Tuple[Literal['message'], MessageCb]
PrefixHookDef: TypeAlias = Tuple[Literal['prefix'], str, MessageCb]
KeywordHookDef: TypeAlias = Tuple[Literal['keyword'], Tuple[str, bool], MessageCb]
MentionHookDef: TypeAlias = Tuple[Literal['account'], Account, MessageCb]
CronHookDef: TypeAlias = Tuple[Literal['cron'], str, CronCb]
AnyCb: TypeAlias = MessageHookDef | PrefixHookDef | KeywordHookDef | MentionHookDef | CronHookDef
"""Any callback definition."""

if TYPE_CHECKING:
    from .protocol import SignalBot
