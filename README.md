# Signal-Bot

An `asyncio` Python 3.11 module for building [Signal][signal] bots that interact with [AsamK/signal-cli][signal-cli].

## Features

* Construct different "personalities" for different contexts (users, groups, etc).
* Callbacks for the following events:
  * Cron schedules.
  * Any message is received.
  * Message matches a prefix (e.g., `/command ...`).
  * Message contains a keyword.
  * Message contains an `@`-mention.
* Currently supported signal-cli functions:
  * "Typing..." indicators.
  * Reacting to messages.
  * Sending messages, including:
    * Inline mentions.
    * Inline text styles.
    * *More to come...*
  * Deleting messages.

## Usage

For development: `python3.11 -m pip install signal_bot_framework`.

```py
# test_bot.py
import asyncio
from signal_bot_framework import create, Account

async def crabby_callback(signal: Signal, context: Context, message: DataMessage) -> bool:
        to = context[1]
        await signal.send_reaction(message, "🦀")
        await signal.send_message(to, f"Sorry, just feeling a little crabby, {message.sender_name}.",
                                  args=SendMessageArgs(mention=[f"37:{len(message.sender_name)}:{message.sender}"]))
        return True

async def main():
    # The default, finds `signal-cli` on path and launches it as a subprocess
    connection = 'ipc://'
    # or, use TCP: connection = 'tcp://HOST:PORT'

    signal = await create(Account('+12345678900'), connection)
    signal.on_keyword('ok?', crabby_callback)
    await signal.run()

if __name__ == '__main__':
    asyncio.run(main())
```

### Docker

For convenience, a base Docker image can be built as `sidneys1/signal_bot`, based on `python:3.11-alpine`.
You can base your bot on it like so:

```Dockerfile
FROM sidneys1/signal_bot:latest

COPY ./test_bot.py .

CMD ["python", "test_bot.py"]
```

You can easily combine this in Docker-Compose with a `signal-cli` container.
Make sure to change your `test_bot.py`'s `connection` string to `tcp://signal-cli:7583`.

Additionally, an easy way to keep your Signal account from being stored in your image or `docker-compose.yml` is to
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

## Building

1. Clone this repository and install the prerequisites:
   * Python >= 3.11 with `venv` support (included with Python for Windows, `python3.11-venv` on most package managers).
   * `python3.11 -m pip install build`
2. Run `python3.11 -m build` in the repository folder.
3. Distribute or install `./dist/signal_bot_framework-X.Y.Z-py3-none-any.whl`.

### Dependencies

* [`cron-converter`][cron-converter] (for Cron-based hooks).
* [`humanize`][humanize] (for debugging output related to Cron-based hooks).

Signal-Bot assumes that you already have `signal-cli` available and registered with an account from which messages will
be sent and received.


<!-- Link definitions -->
[signal]: https://www.signal.org/
[signal-cli]: https://github.com/AsamK/signal-cli
[cron-converter]: https://github.com/Sonic0/cron-converter
[humanize]: https://github.com/python-humanize/humanize
