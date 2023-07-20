"""Signal message arguments."""

from dataclasses import dataclass
from abc import ABC
from typing import Any

from ._util import to_lower_camel_case
from .types import DataMessage

class JsonRpcArgs(ABC):
    """Base class for extended JSON-RPC arguments. Automatically converts to a dict of lowerCamelCase keys to values."""

    def to_args(self):
        """Convert class properties to a dict of lowerCamelCase keys to values."""
        ret = {to_lower_camel_case(x): getattr(self, x)
                for x in dir(self)
                if x[0] != '_' and
                   getattr(self, x) is not None
                   and not callable(getattr(self, x))
                   and not isinstance(getattr(self, x), JsonRpcArgs)}

        for name, nested in ((x, getattr(self, x)) for x in dir(self) if isinstance(getattr(self, x), JsonRpcArgs)):
            ret.update({
                to_lower_camel_case(f"{name}_{k}"): v
                for k, v in nested.to_args().items()
            })
        return ret

@dataclass
class QuoteMessageArgs(JsonRpcArgs):
    """Json representation of a Quoted message."""

    timestamp: int
    author: str
    message: str
    mention: list[str]
    attachments: list[Any]
    text_style: list[str]

    @classmethod
    def from_datamessage(cls, datamessage: DataMessage):
        """Convert a `DataMessage` to a `QuotedMessageArgs`."""
        return QuoteMessageArgs(datamessage.unix_timestamp, datamessage.sender,
                                datamessage.message, datamessage.mentions or [], datamessage.attachments or [],
                                datamessage.text_styles or [])

# @dataclass
# class PreviewMessageArgs(JsonRpcArgs):
#     ...

@dataclass
class SendMessageArgs(JsonRpcArgs):
    """Additional arguments to `send_message`."""

    # note_to_self: bool = False
    # attachment: list[str|Path] = None
    # sticker: str|None = None
    mention: list[str]|None = None
    text_style: list[str]|None = None
    quote: QuoteMessageArgs|None = None
    # preview: PreviewMessageArgs|None = None
    # edit_timestamp: datetime|None = None

