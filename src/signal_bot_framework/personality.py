"""Personalities describe behavior for a subset of :data:`signal_bot_framework.aliases.Context`."""

from __future__ import annotations

from abc import abstractmethod, ABC
from typing import Tuple, Sequence
from datetime import datetime
from logging import getLogger, Logger
import asyncio
import re

import humanize
from cron_converter import Cron
from cron_converter.sub_modules.seeker import Seeker

from .types import AccountNumber, DataMessage
from .protocol import PersonalityProto, MessageCb, CronItem, GroupId, Context, AnyCb, SignalBot, CronCb


class Personality(PersonalityProto, ABC):
    """Specific behavior for a subset of :data:`signal_bot_framework.aliases.Context`."""

    _message_hooks: list[MessageCb]
    _prefix_hooks: dict[str, MessageCb]
    _keyword_hooks: dict[Tuple[str, bool, bool], MessageCb]
    _keyword_cache: dict[Tuple[str, bool, bool], re.Pattern]
    _mention_hooks: dict[AccountNumber, MessageCb]
    _cron_hooks: list[CronItem]
    _crons: list[asyncio.TimerHandle]
    _contexts: Sequence[AccountNumber | GroupId]
    _logger: Logger

    def __init__(self, contexts: Sequence[AccountNumber | GroupId] = tuple()):  # noqa: D107
        self._message_hooks = []
        self._prefix_hooks = {}
        self._keyword_hooks = {}
        self._keyword_cache = {}
        self._mention_hooks = {}
        self._cron_hooks = []
        self._crons = []
        self._contexts = contexts
        self._logger = getLogger(f'{self.__class__.__module__}.{self.__class__.__qualname__}')

    def matches_context(self, context: Context) -> bool:
        """
        Whether or not a given Context is valid for this Personality.

        :param context: The Context in question.
        :type context: :data:`~signal_bot_framework.aliases.Context`
        """
        return len(self._contexts) == 0 or context[1] in self._contexts

    @abstractmethod
    def handle_callback_exception(self, exception: BaseException, cb: AnyCb) -> bool:
        """
        Handle an exception that occured in a callback.

        :param exception: The exception that occurred.
        :param cb: The callback the exception occurred in.
        :type cb: :data:`~signal_bot_framework.aliases.AnyCb`

        :returns: If the callback is a Cron hook, the return value determines whether the Cron will be rescheduled.
        """
        raise NotImplementedError()

    def _cron_repeat(self, signal: SignalBot, schedule: Seeker, item: CronItem):

        def _reschedule(task: asyncio.Task[None]):
            if (ex := task.exception()) is not None and not self.handle_callback_exception(ex, ('cron', *item)):
                return

            loop = asyncio.get_running_loop()
            next_sched = schedule.next()
            delay = (next_sched - datetime.now()).total_seconds()
            self._logger.debug("Cron %r will re-fire %s (%s at %s)", item[0], humanize.naturaltime(next_sched),
                               humanize.naturalday(next_sched), next_sched.strftime("%H:%M:%S"))
            i = 0
            while i < len(self._crons):
                if self._crons[i].when() < loop.time():
                    del self._crons[i]
                    continue
                i += 1
            self._crons.append(loop.call_later(delay, self._cron_repeat, signal, schedule, item))

        asyncio.ensure_future(item[1](signal)).add_done_callback(_reschedule)

    def start_crons(self, signal: 'SignalBot'):
        """
        Start any registered Cron callbacks.

        Called by :class:`~signal_bot_framework.protocol.SignalBot`.

        :param signal: The current :class:`~signal_bot_framework.protocol.SignalBot` instance.
        """
        self._logger.debug("Starting crons...")
        loop = asyncio.get_running_loop()
        ref = datetime.now()
        for item in self._cron_hooks:
            cron_str, _ = item
            cron = Cron(cron_str)
            schedule = cron.schedule(ref)
            next_schedule = schedule.next()
            delay = (next_schedule - ref).total_seconds()
            self._logger.debug("Cron %r will fire %s (%s at %s)", cron_str, humanize.naturaltime(next_schedule),
                               humanize.naturalday(next_schedule), next_schedule.strftime("%H:%M:%S"))
            self._crons.append(loop.call_later(delay, self._cron_repeat, signal, schedule, item))

    def stop_crons(self) -> None:
        """Stop any sleeping Cron callbacks."""
        cron: asyncio.TimerHandle
        for cron in self._crons:
            cron.cancel()

    async def personality_handle_message(self, signal: 'SignalBot', context: Context, message: DataMessage) -> bool:
        """
        Handle a single Signal message that has been approved for this Personality.

        Determines if the message is handled by any of the existing hooks, and if so stops processing.

        :param signal: The current `SignalBot` instance.
        :param context: The context the message was received in.
        :type context: :data:`~signal_bot_framework.aliases.Context`
        :param message: The message that was received.

        :returns: ``True`` if the message was handled by a hook - otherwise the message will be sent to the next
                  Personality in line.
        """
        # First, prefixes
        if message.message is not None:
            for prefix, hook in self._prefix_hooks.items():
                if message.message.startswith(prefix) and await hook(signal, context, message):
                    return True

        # Then mentions
        for account, hook in self._mention_hooks.items():
            if message.mentions and any(mention['number'] == account
                                        for mention in message.mentions) and await hook(signal, context, message):
                return True

        # Then keywords
        if message.message is not None:
            for definition, hook in self._keyword_hooks.items():
                keyword, case_sensitive, whole_word = definition
                if definition in self._keyword_cache:
                    pattern = self._keyword_cache[definition]
                else:
                    pattern = re.compile((r'\b{}\b' if whole_word else '{}').format(re.escape(keyword)),
                                         re.NOFLAG if case_sensitive else re.IGNORECASE)
                    self._keyword_cache[definition] = pattern

                if pattern.search(message.message) and await hook(signal, context, message):
                    return True

        # Finally, global hooks
        for hook in self._message_hooks:
            if await hook(signal, context, message):
                return True

        return False

    def on_message(self, cb: MessageCb):
        self._message_hooks.append(cb)

    # pylint: disable=missing-function-docstring
    def remove_message_callback(self, callback: MessageCb):
        self._message_hooks.remove(callback)

    def on_prefix(self, prefix: str, cb: MessageCb):
        self._prefix_hooks[prefix] = cb

    # pylint: disable=missing-function-docstring
    def remove_prefix(self, prefix: str):
        self._prefix_hooks.pop(prefix, None)

    def on_keyword(self, keyword: str, cb: MessageCb, case_sensitive=False, whole_word=True):
        self._keyword_hooks[keyword, case_sensitive, whole_word] = cb

    # pylint: disable=missing-function-docstring
    def remove_keyword(self, key: str | Tuple[str, bool, bool]):
        for elem in self._keyword_hooks:
            if key == (elem[0] if isinstance(key, str) else elem):
                self._keyword_hooks.pop(elem, None)
                self._keyword_cache.pop(elem, None)
                return

    def on_mention(self, mention: AccountNumber, cb: MessageCb):
        self._mention_hooks[mention] = cb

    # pylint: disable=missing-function-docstring
    def remove_mention(self, mention: AccountNumber):
        self._mention_hooks.pop(mention, None)

    def on_cron(self, schedule: str, cb: CronCb) -> CronItem:
        ret = (schedule, cb)
        self._cron_hooks.append(ret)
        return ret

    # pylint: disable=missing-function-docstring
    def remove_cron(self, item: CronItem):
        self._cron_hooks.remove(item)
