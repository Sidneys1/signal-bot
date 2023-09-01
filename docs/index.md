# Welcome to Signal-Bot's documentation!

Signal-Bot is an `asyncio` Python 3.11 module for building [Signal][signal] bots that interact with
[AsamK/signal-cli][signal-cli].

```{contents} Table of Contents
:depth: 3
```

## Installation and Basic Usage

Install with Pip: `python3.11 -m pip install _framework`.

```py
# test_bot.py
import asyncio
from signal_bot_framework import create, Account

async def do_crabby(signal, context, message):
        await signal.send_reaction(message, "🦀")
        await signal.send_message(context[1], 
            "Sorry, just feeling a little crabby.")
        return True

async def main():
    # The default, finds `signal-cli` on path and launches it
    connection = 'ipc://'
    signal = await create(Account('+12345678900'), connection)
    signal.on_keyword('ok?', do_crabby)
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

```yaml
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

## Building From Source

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

## Modules

```{toctree}
---
maxdepth: 2
glob:
---
signal_bot_framework.md
signal_bot_framework.*
```

## Indices and tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`

[signal]: https://www.signal.org/
[signal-cli]: https://github.com/AsamK/signal-cli
[cron-converter]: https://github.com/Sonic0/cron-converter
[humanize]: https://github.com/python-humanize/humanize
