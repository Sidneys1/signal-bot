# Examples

Examples will use this general format, and some of this boilerpate may be omitted. Additional includes,
functions, or lines of code may be shown in individual examples.

```py
import asycio

from signal_bot_framework import create, AccountNumber, SignalBot
from signal_bot_framework.aliases import Context, DataMessage

async def main():
    """Entrypoint"""

    # Create our Signal-Bot
    signal = await create(AccountNumber('+12345678900'))

    # Run our Signal-Bot.
    await signal.run()

if __name__ == "__main__":
    asyncio.run(main())
```

## Responding to a Prefix, Quoting a Message

```py
# Add these imports:
from signal_bot_framework.args import QuoteMessageArgs, SendMessageArgs

async def main():
    # -snip-

    # Register a callback for messages beginning with "/ping".
    signal.on_prefix('/ping', ping_callback)

    # -snip-

async def ping_callback(signal: SignalBot, context: Context, message: DataMessage) -> bool:
    """Callback for `/ping[...]` messages."""

    # Send a reply - `context[1]` is the chat we're sending a message in,
    # `"Pong!"` is the message we're sending, and `args=...(quote=...)` tells
    # Signal that we're replying to a previous message.
    await signal.send_message(
        context[1],
        "Pong!",
        args=SendMessageArgs(quote=QuoteMessageArgs.from_datamessage(message))
    )

    # Return `True`, meaning that we've handled this `message` and no further
    # callbacks should be processed.
    return True
```

## Using a Cron Callback

Let's register a callback to trigger every day at 7:00 AM EST. First, we must convert the desired time to UTC: 11:00 AM. Then we must create a crontab rule for "11 AM every day": `0 11 * * *` (or, [minute 0, hour 11, every day of the month, every month, every day of the week](https://crontab.guru/#0_11_*_*_*)).

| Minute | Hour | Day of Month |    Month    | Day of Week |
|:------:|:----:|:------------:|:-----------:|:-----------:|
|  `0`   | `11` | `*` (every)  | `*` (every) | `*` (every) |

```py
async def main():
    # -snip-

    # Register a callback to run at 11 AM (UTC).
    signal.on_cron("0 11 * * *", good_morning)

    # -snip-

async def good_morning(signal: SignalBot) -> None:
    """Callback for daily Cron."""

    # Send a message. Since cron callbacks aren't triggered by a specific message,
    # we have to explicitly provide an `AccountNumber`, `AccountUUID`, or `GroupId`.
    await signal.send_message(AccountNumber("+12345678900"), "Good morning!")

    # Cron callbacks don't return a value.
```

## Using Personalities

Signal-Bot allows for the creation of "personalities" to help manage separate behaviors for different audiences.

```py
# Add these imports:
from signal_bot_framework.personality import *

async def main():
    # -snip-

    # Add specific personalities.
    signal.add_personality(FriendsPersonality())
    signal.add_personality(FamilyPersonality())

    # Messages will first be handled by matching personalities - however, we might want to add a catch-all handler to
    # the Signal-Bot client itself to warn us of messages that were not handled.
    signal.on_message(unhandled_message)

    # -snip-

async def unhandled_message(signal: SignalBot, context: Context, message: DataMessage) -> bool:
    print(f'Unhandled message to personality-less context {context!r}: {message!r}')

FAMILY_GROUP = GroupId('...')
DADS_NUMBER = AccountNumber('+...')

FRIEND_GROUP_A = GroupId('...')
FRIEND_GROUP_B = GroupId('...')

class FriendsPersonality(Personality):
    def __init__(self) -> None:
        super().__init__(contexts=[FRIEND_GROUP_A, FRIEND_GROUP_B])
        self.on_mention(AccountNumber("+12345678900"), self.burning_ear)

    async def burning_ear(self, signal: SignalBot, context: Context, message: DataMessage) -> bool:
        """Let people know I'm listening."""
        await signal.send_reaction(message, "👂")
        return True

class FamilyPersonality(Personality):
    def __init__(self) -> None:
        super().__init__(contexts=[FAMILY_GROUP, DADS_NUMBER])
        self.on_mention(AccountNumber("+12345678900"), self.burning_ear)

    async def burning_ear(self, signal: SignalBot, context: Context, message: DataMessage) -> bool:
        """Let people know I'm listening."""
        await signal.send_reaction(message, "🥰")
        return True
```
