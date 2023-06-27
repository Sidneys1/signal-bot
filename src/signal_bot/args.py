"""Signal message arguments."""

from dataclasses import dataclass
from abc import ABC

from ._util import to_lower_camel_case

class JsonRpcArgs(ABC):
    """Base class for extended JSON-RPC arguments. Automatically converts to a dict of lowerCamelCase keys to values."""

    def to_args(self):
        """Convert class properties to a dict of lowerCamelCase keys to values."""
        return {to_lower_camel_case(x): getattr(self, x)
                for x in dir(self)
                if x[0] != '_' and 
                   getattr(self, x) is not None 
                   and not callable(getattr(self, x))}

# @dataclass
# class QuoteMessageArgs(JsonRpcArgs):
#     ...

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
    # quote: QuoteMessageArgs|None = None
    # preview: PreviewMessageArgs|None = None
    # edit_timestamp: datetime|None = None

