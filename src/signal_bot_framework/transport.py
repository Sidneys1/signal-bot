"""Handles communication with ``signal-cli``."""

import json
from typing import Self, Protocol, Dict, Type, Iterable, cast
from abc import abstractmethod
import asyncio.subprocess
from asyncio import CancelledError, open_connection, StreamReader, StreamWriter
from urllib.parse import ParseResult, unquote
from subprocess import PIPE

from .constants import SIGNAL_ARGS, JSON_PROPS
from .types import NotificationFrame, ResponseFrame
from ._util import readline


class JsonRpcHandler(Protocol):
    """
    Notified by `JsonRpcTransport` of incoming JSON RPC responses and notifications.

    This abstract Protocol is implemented by :class:`~signal_bot_framework.protocol.SignalBot`.
    """

    async def handle_notification(self, notification: NotificationFrame) -> None:
        """
        Handle a JSON-RPC notification (a message that is not a response to a request).

        :param notification: The notification that was received.
        """

    async def handle_response(self, response: ResponseFrame) -> None:
        """
        Handle a JSON-RPC response (the result of a request).

        :param response: The response that was received.
        """


class JsonRpcTransport(Protocol):
    """Allows for communication with signal-cli."""

    PROTOS: Dict[str, Type[Self]] = {}

    @classmethod
    @abstractmethod
    async def create(cls, connection: ParseResult) -> Self:
        """
        Create an instance of this transport.

        :param connection: ``urllib`` parsed connections string.
        """

    def __init_subclass__(cls, /, scheme: str | Iterable[str], *args, **kwargs) -> None:
        if isinstance(scheme, str):
            JsonRpcTransport.PROTOS[scheme] = cls  # type: ignore
        else:
            JsonRpcTransport.PROTOS.update({x: cls for x in scheme})  # type: ignore
        return super().__init_subclass__(*args, **kwargs)

    @abstractmethod
    async def write(self, data: NotificationFrame) -> None:
        """
        Write a notification to ``signal-cli``.

        :param data: The notification to send.
        """

    @abstractmethod
    async def listen(self, handler: JsonRpcHandler) -> None:
        """
        Listen for notifications and responses from ``signal-cli``.

        :param handler: The class that will handle any received notifications or responses.
        """

    async def terminate(self) -> None:
        """
        Terminate the connection to ``signal-cli`` (if necessary).
        """


class TcpTransport(JsonRpcTransport, scheme='tcp'):
    """:class:`JsonRpcTransport` for the ``tcp://`` scheme."""

    __reader: StreamReader
    __writer: StreamWriter

    @classmethod
    async def create(cls, connection: ParseResult) -> Self:
        return cls(await open_connection(connection.hostname, connection.port))

    def __init__(self, connection: tuple[StreamReader, StreamWriter]) -> None:
        self.__reader, self.__writer = connection

    async def write(self, data: NotificationFrame) -> None:
        self.__writer.write(json.dumps(data, **JSON_PROPS).encode('utf-8') + b'\n')  # type: ignore
        await self.__writer.drain()

    async def listen(self, handler: JsonRpcHandler) -> None:
        try:
            while True:
                line = await readline(self.__reader, timeout=0.1)
                if line is None:
                    continue
                obj: NotificationFrame | ResponseFrame = json.loads(line)
                match obj:
                    case {'result': _} | {'error': _}:
                        await handler.handle_response(cast(ResponseFrame, obj))
                    case _:
                        await handler.handle_notification(cast(NotificationFrame, obj))
        except CancelledError:
            pass


# class HttpTransport(JsonRpcTransport, scheme=('http', 'https')):
#     __session: aiohttp.ClientSession

#     @classmethod
#     async def create(cls, connection: ParseResult) -> Self:
#         return cls(urlunparse(connection))

#     def __init__(self, url: str) -> None:
#         self.__session = aiohttp.ClientSession(url)

#     async def write(self, data: NotificationFrame, handler: JsonRpcHandler) -> None:
#         async with self.__session.post('', json.dumps(data, **JSON_PROPS).encode('utf-8')) as response:
#             await handler.handle_response(cast(ResponseFrame, json.loads(response.text())))

# async def listen(self, data: )


class SubprocessTransport(JsonRpcTransport, scheme='ipc'):
    """:class:`JsonRpcTransport` for the ``ipc://`` (interprocess communication) scheme."""

    __signal_cli: asyncio.subprocess.Process  # pylint: disable=no-member

    @classmethod
    async def create(cls, connection: ParseResult) -> Self:
        path: str | None
        if connection.path:
            path = unquote(connection.path)
        else:
            from shutil import which
            path = which('signal-cli')
            if path is None:
                raise RuntimeError('could not find `signal-cli` on PATH')

        # pylint: disable=no-member
        process = await asyncio.subprocess.create_subprocess_exec(path,
                                                                  'jsonRpc',
                                                                  *SIGNAL_ARGS,
                                                                  stdin=PIPE,
                                                                  stdout=PIPE,
                                                                  stderr=PIPE)
        return cls(process)

    def __init__(self, signal_cli: asyncio.subprocess.Process) -> None:  # pylint: disable=no-member
        self.__signal_cli = signal_cli

    async def write(self, data: NotificationFrame) -> None:
        stdin = self.__signal_cli.stdin
        assert stdin is not None
        stdin.write(json.dumps(data, **JSON_PROPS).encode('utf-8') + b'\n')  # type: ignore
        await stdin.drain()

    async def listen(self, handler: JsonRpcHandler) -> None:
        stdout = self.__signal_cli.stdout
        assert stdout is not None
        assert handler is not None
        try:
            while True:
                line = await readline(stdout, timeout=0.1)
                if line is None:
                    continue
                obj: NotificationFrame | ResponseFrame = json.loads(line)
                match obj:
                    case {'result': _} | {'error': _}:
                        await handler.handle_response(cast(ResponseFrame, obj))
                    case _:
                        await handler.handle_notification(cast(NotificationFrame, obj))
        except CancelledError:
            pass
