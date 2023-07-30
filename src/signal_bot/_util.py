"""Signal-Bot internal helpers."""

import asyncio


async def readline(stream: asyncio.StreamReader, timeout: float|None = None) -> bytes | None:
    """
    Read a single line from a `StreamReader`, with a timeout.

    :param stream: The stream to read from.
    :param timeout: The maximum time to wait for a line to be read.
    """
    try:
        return await asyncio.wait_for(stream.readline(), timeout=timeout)
    except asyncio.TimeoutError:
        return None


def to_camel_case(snake_str: str) -> str:
    """
    Convert a snake_case string to CamelCase.

    :param snake_str: The string to convert.
    """
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))


def to_lower_camel_case(snake_str: str) -> str:
    """
    Convert a snake_case string to lowerCamelCase.
    
    :param snake_str: The string to convert.
    """
    return snake_str[0].lower() + to_camel_case(snake_str)[1:]
