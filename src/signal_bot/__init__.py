"""signal_bot: An async Signal messenger bot framework, utilizing signal-cli."""

from urllib.parse import urlparse

from .types import *
from .exceptions import *
from .protocol import SignalBot
from .transport import JsonRpcTransport


####################################################
# Looking for documentation? Check out the README: #
#      https://github.com/Sidneys1/signal-bot      #
####################################################


#################################################################
# Looking for high-level interfaces? Check out `./protocol.py`. #
#################################################################


async def create(account: Account, connection: str = 'ipc://') -> SignalBot:
    """Create an instance of `SignalBot`."""
    parts = urlparse(connection)
    try:
        transport_class = JsonRpcTransport.PROTOS[parts.scheme]
    except KeyError:
        raise NotImplementedError(f'Connection scheme {parts.scheme!r} has not been implemented ({", ".join(JsonRpcTransport.PROTOS)}).')
    from ._signal_impl import SignalBotImpl
    return SignalBotImpl(account, await transport_class.create(parts))
