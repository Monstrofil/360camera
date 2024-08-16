import asyncio
import typing


class event:
    def __init__(self, func: typing.Callable):
        self._handlers = []

    def add(self, handler: typing.Callable):
        self._handlers.append(handler)

    def remove(self, handler: typing.Callable):
        self._handlers.remove(handler)

    async def __call__(self, *args, **kwargs):
        for handler in self._handlers:
            await asyncio.create_task(handler(*args, **kwargs))
