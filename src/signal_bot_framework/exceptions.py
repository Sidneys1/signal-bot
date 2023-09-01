"""Exceptions used by `signal_bot_framework`."""


class SignalRpcException(Exception):
    """Occurs when the response to a JSON-RPC request is an error."""

    message: str
    """The error message."""

    body: dict
    """The raw JSON-RPC error body."""

    def __init__(self, message: str, body: dict):  # noqa: D107
        self.message = message
        self.body = body
