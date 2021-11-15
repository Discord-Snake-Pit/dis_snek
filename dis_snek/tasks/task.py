import asyncio
import inspect
import logging
from asyncio import AbstractEventLoop, Future, TimerHandle
from asyncio import Task as _Task
from datetime import datetime, timedelta
from typing import Callable, Optional

from dis_snek.const import logger_name, MISSING
from dis_snek.tasks.triggers import BaseTrigger

log = logging.getLogger(logger_name)


class Sleeper:
    __slots__ = "_loop", "future", "handle"
    loop: AbstractEventLoop
    future: Future
    handle: TimerHandle

    def __init__(self, event_loop: AbstractEventLoop):
        self._loop = event_loop

    def __call__(self, until: datetime):
        self.future = self._loop.create_future()

        delta = until - datetime.now()
        self.handle = self._loop.call_later(delta.total_seconds(), self.future.set_result, True)
        return self.future

    def cancel(self):
        self.handle.cancel()
        self.future.cancel()


class Task:
    """
    Create an asynchronous background tasks. Tasks allow you to run code according to a trigger object.

    A task's trigger must inherit from `BaseTrigger`.
    """

    callback: Callable
    trigger: BaseTrigger
    sleeper: Sleeper
    task: _Task
    _stop: bool

    def __init__(self, callback: Callable, trigger: BaseTrigger):
        self.callback = callback
        self.trigger = trigger
        self._stop = False
        self.task = MISSING
        self.sleeper = MISSING

    @property
    def _loop(self) -> AbstractEventLoop:
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            log.error("Unable to start task! Event loop is not running yet!")
            self.stop()

    @property
    def next_run(self) -> Optional[datetime]:
        """Get the next datetime this task will run"""
        if not self.task.done():
            return self.trigger.next_run()
        return None

    @property
    def delta_until_run(self) -> Optional[timedelta]:
        if not self.task.done():
            return self.next_run - datetime.now()

    def __call__(self):
        if inspect.iscoroutinefunction(self.callback):
            asyncio.ensure_future(self.callback())
        else:
            self.callback()

    def _fire(self, fire_time: datetime):
        """Called when the task is being fired"""
        self.trigger.last_call_time = fire_time
        self()

    async def _task_loop(self):
        while not self._stop:
            fire_time = self.trigger.next_run()
            if fire_time is None:
                self.stop()
            if datetime.now() > fire_time:
                self._fire(fire_time)
                await self.sleeper(self.trigger.next_run())
            else:
                await self.sleeper(self.trigger.next_run())

    def start(self):
        """Start this task"""
        self._stop = False
        if self._loop:
            self.sleeper = Sleeper(self._loop)
            self.task = asyncio.create_task(self._task_loop())

    def stop(self):
        """End this task"""
        self._stop = True
        if self.task:
            self.task.cancel()
        if self.sleeper:
            self.sleeper.cancel()

    @classmethod
    def create(cls, trigger: BaseTrigger) -> Callable[[Callable], "Task"]:
        """
        A decorator to create a task

        Args:
            trigger: The trigger to use for this task
        """

        def wrapper(func: Callable):
            return cls(func, trigger)

        return wrapper
