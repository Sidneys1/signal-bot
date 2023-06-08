import asyncio
from logging import getLogger
from typing import TypeVar, Generic, Callable, Optional
from types import EllipsisType


def static_vars(**kwargs):
    """
    Add static variables to a method. E.g.:
    ```
    @static_vars(foo=1)
    def bar():
        return bar.foo  # returns 1
    ```
    """
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


async def readline(stream: asyncio.StreamReader, timeout: Optional[float] = None) -> bytes | None:
    try:
        return await asyncio.wait_for(stream.readline(), timeout=timeout)
    except asyncio.TimeoutError:
        return None
    except asyncio.CancelledError:
        raise


def to_camel_case(snake_str):
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))

def to_lower_camel_case(snake_str):
    return snake_str[0].lower() + to_camel_case(snake_str)[1:]