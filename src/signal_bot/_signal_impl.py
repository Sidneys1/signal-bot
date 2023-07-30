"""Signal-Bot implementation."""

import asyncio
from asyncio import Future
from uuid import uuid4
from logging import Logger, getLogger
from datetime import datetime
from inspect import isawaitable
from typing import Dict, Hashable, Callable, cast

from .types import Account, DataMessage, Response, GroupId, ResponseFrame, NotificationFrame, EnvelopeFrame
from .aliases import GroupContext, AnyCb, IndividualContext
from .args import SendMessageArgs
from .exceptions import SignalRpcException
from .personality import Personality
from .protocol import SignalBot, PersonalityProto, RpcRet
from .transport import JsonRpcTransport, JsonRpcHandler


class SignalBotImpl(SignalBot, Personality, JsonRpcHandler):
    """Concrete implementation of `SignalBot`."""

    __account: Account
    __transport: JsonRpcTransport
    __log: Logger = getLogger(__module__ + '.Signal')  # type: ignore
    __start_time: datetime
    __personalities: list[Personality]
    __stopping = asyncio.Event()
    __cancelable: list[asyncio.Task | asyncio.Handle]

    def __init__(self, account: Account, transport: JsonRpcTransport) -> None:
        self.__account = account
        self.__transport = transport
        self.__start_time = datetime.now()
        self.__personalities = []
        self.__cancelable = []
        Personality.__init__(self)

    # `Signal`

    @property
    def account(self) -> Account:
        return self.__account

    async def run(self) -> None:
        self.start_crons(self)
        for personality in self.__personalities:
            personality.start_crons(self)
            asyncio.ensure_future(personality.started(self))
        try:
            await self.__transport.listen(self)
        except asyncio.CancelledError:
            self.__log.debug('Transport listen loop stopped.')
            await self.stop()

    async def stop(self) -> None:
        if self.__stopping.is_set():
            return
        self.__log.info("Stop requested...")
        self.__log.debug("Stopping Crons...")
        self.__stopping.set()
        self.stop_crons()
        for personality in self.__personalities:
            personality.stop_crons()
        self.__log.debug("Disconnecting from signal-cli...")
        await self.__transport.terminate()
        self.__log.debug("Canceling anything in-flight...")
        if self.__cancelable:
            for cancelable in self.__cancelable:
                cancelable.cancel()
            self.__log.debug("Waiting for cancelables to finish...")
            await asyncio.wait([x for x in self.__cancelable if isawaitable(x)])
        self.__log.info("Stopped.")
        self.__stopping.clear()

    #######################
    # `SignalRpc` Methods #
    #######################

    async def send_reaction(self, to: DataMessage, emoji: str) -> Future[Response]:
        kwargs = {}
        if to.group_info is None:
            kwargs['recipient'] = to.sender
        else:
            kwargs['groupId'] = to.group_info['groupId']  # type: ignore

        return asyncio.ensure_future(
            Response.from_future_frame(await self.__json_rpc('sendReaction',
                                                             emoji=emoji,
                                                             targetAuthor=to.sender,
                                                             targetTimestamp=to.unix_timestamp,
                                                             **kwargs)))

    async def send_typing(self, to: Account | GroupId, stop=False) -> Future[Response]:
        kwargs: dict = {('groupId' if len(to) == 44 else 'recipient'): to}
        if stop:
            kwargs['stop'] = True
        return asyncio.ensure_future(Response.from_future_frame(await self.__json_rpc('sendTyping', **kwargs)))

    async def send_message(self,
                           to: Account | GroupId,
                           message: str | None = None,
                           args: SendMessageArgs | None = None) -> Future[Response]:
        if (not message) and args is not None and not args.attachment:
            raise ValueError('message cannot be empty without attachment')
        kwargs: dict = {('groupId' if len(to) == 44 else 'recipient'): to}
        if args is not None:
            kwargs.update(args.to_args())
        return asyncio.ensure_future(
            Response.from_future_frame(await self.__json_rpc('send', message=message, **kwargs)))

    async def delete_message(self, to: Account | GroupId, target_timestamp: datetime) -> RpcRet:
        kwargs: dict = {
            ('groupId' if len(to) == 44 else 'recipient'): to,
            'targetTimestamp': int(target_timestamp.timestamp() * 1000)
        }
        return asyncio.ensure_future(Response.from_future_frame(await self.__json_rpc('remoteDelete', **kwargs)))

    def add_personality(self, personality: PersonalityProto) -> None:
        assert isinstance(personality, Personality)
        self.__personalities.append(personality)

    def handle_callback_exception(self, exception: BaseException, cb: AnyCb) -> bool:
        callback_type, *info = cb
        post = "" if callback_type != 'cron' else " Cron will be rescheduled for the next occurance."
        self.__log.exception("Uncaught exception while processing a registered %r callback (addt'l info: %r).%s",
                             callback_type,
                             info,
                             post,
                             exc_info=exception,
                             stack_info=True)
        return True

    ############################
    # `JsonRpcHandler` Methods #
    ############################

    async def handle_response(self, response: ResponseFrame) -> None:
        remove = next((id for id, checker in self.__WAITERS.items() if checker(response)), None)
        if remove is not None:
            del self.__WAITERS[remove]

    async def handle_notification(self, notification: NotificationFrame) -> None:
        match notification['method']:
            case 'receive':
                await self.__receive(notification)
            case _:
                self.__log.warning('Received unexpected JsonRPC notification method: %r', notification['method'])

    #############
    # Internals #
    #############

    async def __receive(self, message: NotificationFrame) -> None:
        # TODO: logging
        envelope: EnvelopeFrame = message['params'].get('envelope', None)
        if envelope is None:
            # TODO: logging
            return

        # source = envelope['source']
        # source_name = envelope['sourceName'] or source
        timestamp = datetime.fromtimestamp(envelope['timestamp'] / 1000.0)
        if timestamp <= self.__start_time:
            # TODO: catchup mode?
            return

        match envelope:
            case {'typingMessage': _}:
                # TODO: self.__handle_typing_message(envelope)
                pass
            case {'dataMessage': _}:
                asyncio.create_task(self.__handle_data_message(envelope))
            case _:
                # TODO: logging
                pass

    async def __handle_data_message(self, envelope: EnvelopeFrame) -> None:
        if envelope['dataMessage']['message'] is None:
            return

        message = DataMessage(envelope)
        context: GroupContext | IndividualContext
        if message.group_info is not None:
            context = ('group', GroupId(message.group_info['groupId']))
        else:
            context = ('individual', message.sender, envelope['sourceName'])

        for personality in self.__personalities:
            if personality.matches_context(context) and await personality.personality_handle_message(
                    self, context, message):
                return
        await self.personality_handle_message(self, context, message)

    __WAITERS: Dict[Hashable, Callable[[ResponseFrame], bool]] = {}

    async def __json_rpc(self, method: str, **params) -> Future[ResponseFrame]:
        request_id = params.pop("request_id", str(uuid4()))
        if not params:
            params = {}

        params.update({"account": self.__account})
        request: NotificationFrame = {
            'jsonrpc': '2.0',
            'id': request_id,
            'method': method,
            'params': params,
        }

        loop = asyncio.get_running_loop()
        future: Future[ResponseFrame] = loop.create_future()
        key = object()

        def cancel_timer():
            """Cancels our RPC after a timeout"""
            if not future.done():
                future.set_exception(TimeoutError(f"request id {request_id!r} timed out"))
                self.__WAITERS.pop(key, None)

        t_handle = loop.call_later(5.0, cancel_timer)
        self.__cancelable.append(t_handle)

        def check_return(ret: ResponseFrame) -> bool:
            if ret['id'] != request_id:
                return False
            match ret:
                case {'error': error}:
                    self.__log.debug("Setting exception %r", error)
                    future.set_exception(SignalRpcException(error['message'], cast(dict, ret)))
                case _:
                    self.__log.debug("Setting result %r", ret)
                    future.set_result(ret)
            t_handle.cancel()
            self.__cancelable.remove(t_handle)
            return True

        self.__WAITERS[key] = check_return
        self.__log.debug(request)
        self.__cancelable.append(loop.create_task(self.__transport.write(request)))
        return future
