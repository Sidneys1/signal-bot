import json
from typing import Self, cast
from asyncio import subprocess, CancelledError, open_connection, StreamReader, StreamWriter
from urllib.parse import ParseResult, unquote, urlunparse
from subprocess import PIPE
# import aiohttp

from .constants import SIGNAL_ARGS, JSON_PROPS
from .protocol import JsonRpcTransport, JsonRpcHandler
from .types import NotificationFrame, ResponseFrame
from ._util import readline


class TcpTransport(JsonRpcTransport, scheme='tcp'):
    __reader: StreamReader
    __writer: StreamWriter

    @classmethod
    async def create(cls, connection: ParseResult) -> Self:
        return cls(await open_connection(connection.hostname, connection.port))

    def __init__(self, connection: tuple[StreamReader, StreamWriter]) -> None:
        self.__reader, self.__writer = connection

    async def write(self, data: NotificationFrame, _: JsonRpcHandler) -> None:
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
    __signal_cli: subprocess.Process

    @classmethod
    async def create(cls, connection: ParseResult) -> Self:
        if connection.path:
            path = unquote(connection.path)
        else:
            from shutil import which
            path = which('signal-cli')
            if path is None:
                raise RuntimeError('could not find `signal-cli` on PATH')
        
        process = await subprocess.create_subprocess_exec(path, 'jsonRpc', *SIGNAL_ARGS, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        return cls(process)

    def __init__(self, signal_cli: subprocess.Process) -> None:
        self.__signal_cli = signal_cli

    async def write(self, data: NotificationFrame, _: JsonRpcHandler) -> None:
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