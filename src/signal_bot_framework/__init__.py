"""
`signal_bot_framework`: An async Signal messenger bot framework, utilizing `signal-cli`.

Get started with :meth:`signal_bot_framework.create`.

Looking for high-level interfaces? Check out :mod:`signal_bot_framework.protocol`.
"""

from urllib.parse import urlparse

from .version import __version__
from .types import AccountNumber
from .protocol import SignalBot
from .transport import JsonRpcTransport


####################################################
# Looking for documentation? Check out the README: #
#      https://github.com/Sidneys1/signal-bot      #
####################################################

#################################################################
# Looking for high-level interfaces? Check out `./protocol.py`. #
#################################################################
async def create(account: AccountNumber, connection: str = 'ipc://') -> SignalBot:
    """
    Create an instance of `SignalBot`.

    :param account: The Signal account to use (e.g., `"+12345678901"`).
    :type account: :data:`~signal_bot_framework.types.AccountNumber`

    :param connection: The connection string used to communicate with `signal-cli`. See classes in
                       :mod:`signal_bot_framework.transport` for supported forms.

    :raises NotImplementedError: When the URI scheme in :paramref:`connection` is not supported by an existing
                                 :class:`~signal_bot_framework.transport.JsonRpcTransport`.
    """
    parts = urlparse(connection)
    try:
        transport_class = JsonRpcTransport.PROTOS[parts.scheme]  # type: ignore
    except KeyError as ex:
        extra = ", ".join(JsonRpcTransport.PROTOS)  # type: ignore
        raise NotImplementedError(f'Connection scheme {parts.scheme!r} has not been '
                                  f'implemented (recognized: {extra}).') from ex
    from ._signal_impl import SignalBotImpl
    return SignalBotImpl(account, await transport_class.create(parts))  # type: ignore
