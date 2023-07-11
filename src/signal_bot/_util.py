import asyncio


async def readline(stream: asyncio.StreamReader, timeout: float|None = None) -> bytes | None:
    """Read a single line from a `StreamReader`, with a timeout."""
    try:
        return await asyncio.wait_for(stream.readline(), timeout=timeout)
    except asyncio.TimeoutError:
        return None
    except asyncio.CancelledError:
        raise


def to_camel_case(snake_str):
    """Convert a snake_case string to CamelCase."""
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))


def to_lower_camel_case(snake_str):
    """Convert a snake_case string to lowerCamelCase."""
    return snake_str[0].lower() + to_camel_case(snake_str)[1:]