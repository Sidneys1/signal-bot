# Signal-Bot

A fully `asyncio` Python 3.11 module for building [Signal][signal-org] bots that interact with [`signal-cli`][signal-cli].

Dependencies:
 - [`cron-converter`][cron-converter]
 - [`humanize`](humanize)

Signal-Bot assumes that you already have `signal-cli` available and registered with an account from which messages will
be sent and received.

### Currently supported functions:
* Sending reactions to messages.
* Sending/stopping "typing..." indicators.
* Sending messages, including:
    * Inline mentions.
    * Inline text styles.
* Deleting messages.

## Building

1. Clone this repostory and install the prerequisites:
   * Python >= 3.11 with venv support (included with Python for Windows, `python3.11-venv` on most package managers)
   * `python3.11 -m pip install build`
2. Run `python3.11 -m build` in the repository folder.
3. Distribute or install `./dist/signal_bot-X.Y.Z-py3-none-any.whl`.

## Usage

For development: `python3.11 -m pip install signal_bot`.

```py
# test_bot.py
import asyncio
from random import random

from signal_bot import create, Account, Personality


class TestPersonality(Personality):
    def __init__(self) -> None:
        super().__init__(contexts=(Account('+12345678900'), GroupId('4zzZXsS2dXB+kF5Jj9Rvst78wZcFCvfo46iw9I9VcCA=')))
        self.on_keyword('ok?', self.crabby)

    async def crabby(self, signal: Signal, context: Context, message: DataMessage) -> bool:
        to = context[1]
        await signal.send_reaction(message, "🦀")
        await asyncio.sleep(random() * 0.75 + 0.25)
        await signal.send_typing(to)
        await asyncio.sleep(random() * 2 + 0.5)
        args = SendMessageArgs(mention=[f"18:{len(message.sender_name)}:{message.sender}"])
        await signal.send_message(to, f"Sorry, just feeling a little crabby, {message.sender_name}.", args=args)
        return True

    def handle_callback_exception(self, exception: BaseException, callback: AnyCb) -> bool:
        print("Uncaught exception in test personality for %r callback (%r)", callback[0], callback[1:])
        return True


async def main():
    # The default, finds `signal-cli` on path and launches it as a subprocess
    connection = 'ipc://'
    # or, use TCP: connection = 'tcp://HOST:PORT'

    signal = await create(Account('+12345678900'), connection)
    signal.add_personality(TestPersonality())

    await signal.run()


if __name__ == '__main__':
    asyncio.run(main())
```

### Docker

For convenience, a base docker image is available as `sidneys1/signal_bot`, based on `python:3.11-alpine`.
You can base your bot on it like so:

```Dockerfile
FROM sidneys1/signal_bot:latest

COPY ./test_bot.py .

CMD ["python", "test_bot.py"]
```

You can easily combine this in Docker-Compose with a `signal-cli` container.
Make sure to change your `test_bot.py`'s `connection` string to `tcp://signal-cli:7583`.
Additionaly, an easy way to keep your Signal account from being stored in your container or `docker-compose.yml` is to
store it in a Docker secret, as shown below.

```yml
secrets:
  signal-account:
    file: .signal-account

services:
  test_bot:
    build: .
    depends_on: [signal-cli]
  signal-cli:
    image: registry.gitlab.com/packaging/signal-cli/signal-cli-native:latest
    volumes:
     # Mount an existing signal-cli configuration directory from the host.
     - "${HOME}/.local/share/signal-cli:/var/lib/signal-cli:rw"
    ports: ["7583"]
    secrets: [signal-account]
    entrypoint: sh -c
    command: "'signal-cli -c /var/lib/signal-cli --account $(cat /run/secrets/signal-account) daemon --receive-mode on-connection --no-receive-stdout --send-read-receipts --tcp 0.0.0.0:7583'"
```

<!-- Link definitions -->
[signal-org]: https://www.signal.org/
[signal-cli]: https://github.com/AsamK/signal-cli
[cron-converter]: https://github.com/Sonic0/cron-converter
[humanize]: https://github.com/python-humanize/humanize