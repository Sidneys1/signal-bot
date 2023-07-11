from abc import abstractmethod, ABC
from typing import Tuple, Sequence
from datetime import datetime
from logging import getLogger, Logger
import asyncio
import re

import humanize
from cron_converter import Cron
from cron_converter.sub_modules.seeker import Seeker

from .types import *
from .protocol import *


class Personality(PersonalityProto, ABC):
    _message_hooks: list[MessageCb]
    _prefix_hooks: dict[str, MessageCb]
    _keyword_hooks: dict[Tuple[str, bool, bool], MessageCb]
    _keyword_cache: dict[Tuple[str, bool, bool], re.Pattern]
    _mention_hooks: dict[Account, MessageCb]
    _cron_hooks: list[CronItem]
    _crons: list[asyncio.TimerHandle]
    _contexts: Sequence[Account | GroupId]
    _logger: Logger

    def __init__(self, contexts: Sequence[Account | GroupId] = tuple()):
        self._message_hooks: list[MessageCb] = []
        self._prefix_hooks: dict[str, MessageCb] = {}
        self._keyword_hooks: dict[Tuple[str, bool, bool], MessageCb] = {}
        self._keyword_cache: dict[Tuple[str, bool, bool], re.Pattern] = {}
        self._mention_hooks: dict[Account, MessageCb] = {}
        self._cron_hooks: list[CronItem] = []
        self._crons: list[asyncio.TimerHandle] = []
        self._contexts: Sequence[Account | GroupId] = contexts
        self._logger = getLogger(f'{self.__class__.__module__}.{self.__class__.__qualname__}')

    def matches_context(self, context: Context) -> bool:
        return context[1] in self._contexts

    @abstractmethod
    def handle_callback_exception(self, exception: BaseException, callback: AnyCb) -> bool:
        """
        Called when a exception occurs in a callback.
        If the callback is a Cron hook, the return value determines whether the
        Cron will be rescheduled (True == yes).
        """
        raise NotImplementedError()

    def _cron_repeat(self, signal: 'SignalBot', schedule: Seeker, item: CronItem):
        def _reschedule(task: asyncio.Task[None]):
            if (ex := task.exception()) is not None and not self.handle_callback_exception(ex, ('cron', *item)):
                return

            loop = asyncio.get_running_loop()
            next = schedule.next()
            delay = (next - datetime.now()).total_seconds()
            self._logger.debug("Cron %r will re-fire %s (%s at %s)", item[0], humanize.naturaltime(next),
                                humanize.naturalday(next), next.strftime("%H:%M:%S"))
            i = 0
            while i < len(self._crons):
                if self._crons[i].when() < loop.time():
                    del self._crons[i]
                    continue
                i += 1
            self._crons.append(loop.call_later(delay, self._cron_repeat, signal, schedule, item))
        asyncio.ensure_future(item[1](signal)).add_done_callback(_reschedule)

    def start_crons(self, signal: 'SignalBot'):
        self._logger.debug("Starting crons...")
        loop = asyncio.get_running_loop()
        ref = datetime.now()
        for item in self._cron_hooks:
            cron_str, callback = item
            cron = Cron(cron_str)
            schedule = cron.schedule(ref)
            next = schedule.next()
            delay = (next - ref).total_seconds()
            self._logger.debug("Cron %r will fire %s (%s at %s)", cron_str, humanize.naturaltime(next),
                               humanize.naturalday(next), next.strftime("%H:%M:%S"))
            self._crons.append(loop.call_later(delay, self._cron_repeat, signal, schedule, item))

    def stop_crons(self) -> None:
        cron: asyncio.TimerHandle
        for cron in self._crons:
            cron.cancel()

    async def _personality_handle_message(self, signal: 'SignalBot', context: Context, message: DataMessage) -> bool:
        # First, prefixes
        if message.message is not None:
            for prefix, hook in self._prefix_hooks.items():
                if message.message.startswith(prefix) and await hook(signal, context, message):
                    return True

        # Then mentions
        for account, hook in self._mention_hooks.items():
            if message.mentions and any(mention['number'] == account for mention in message.mentions) and await hook(signal, context, message):
                return True

        # Then keywords
        if message.message is not None:
            for definition, hook in self._keyword_hooks.items():
                keyword, case_sensitive, whole_word = definition
                if definition in self._keyword_cache:
                    pattern = self._keyword_cache[definition]
                else:
                    pattern = re.compile((r'\b{}\b' if whole_word else '{}').format(re.escape(keyword)), re.NOFLAG if case_sensitive else re.IGNORECASE)
                    self._keyword_cache[definition] = pattern
                
                if pattern.search(message.message) and await hook(signal, context, message):
                    return True

        # Finally, global hooks
        for hook in self._message_hooks:
            if await hook(signal, context, message):
                return True
            
        return False

    def on_message(self, callback: MessageCb):
        self._message_hooks.append(callback)

    def remove_message_callback(self, callback: MessageCb):
        self._message_hooks.remove(callback)

    def on_prefix(self, prefix: str, callback: MessageCb):
        self._prefix_hooks[prefix] = callback

    def remove_prefix(self, prefix: str):
        self._prefix_hooks.pop(prefix, None)

    def on_keyword(self, keyword: str, callback: MessageCb, case_sensitive = False, whole_word = True):
        self._keyword_hooks[keyword, case_sensitive, whole_word] = callback

    def remove_keyword(self, key: str|Tuple[str, bool, bool]):
        for elem in self._keyword_hooks:
            if key == (elem[0] if isinstance(key, str) else elem):
                self._keyword_hooks.pop(elem, None)
                self._keyword_cache.pop(elem, None)
                return

    def on_mention(self, mention: Account, callback: MessageCb):
        self._mention_hooks[mention] = callback

    def remove_mention(self, mention: Account):
        self._mention_hooks.pop(mention, None)

    def on_cron(self, schedule: str, callback: CronCb) -> CronItem:
        ret = (schedule, callback)
        self._cron_hooks.append(ret)
        return ret

    def remove_cron(self, item: CronItem):
        self._cron_hooks.remove(item)