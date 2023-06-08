from urllib.parse import urlparse

from .types import *
from .exceptions import *
from .protocol import Signal
from .transport import JsonRpcTransport

# Looking for documentation? Check out the README:
#   https://github.com/Sidneys1/signal-bot

async def create(account: Account, connection: str = 'ipc://') -> Signal:
    parts = urlparse(connection)
    try:
        transport_class = JsonRpcTransport.PROTOS[parts.scheme]
    except KeyError:
        raise NotImplementedError(f'Connection scheme {parts.scheme!r} has not been implemented ({", ".join(JsonRpcTransport.PROTOS)}).')
    from ._signal_impl import SignalImpl
    return SignalImpl(account, await transport_class.create(parts))
