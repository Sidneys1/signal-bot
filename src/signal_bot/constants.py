"""Constants used internally to `signal_bot`."""

SIGNAL_ARGS = ['--ignore-attachments', '--ignore-stories', '--send-read-receipts']
"""Default arguments passed to `signal-cli` when running in `ipc:` mode."""

JSON_PROPS = {
    'ensure_ascii': True,
    'indent': None,
    'separators': (',', ':'),
}
"""The default arguments passed to `json.dumps` when creating JSON-RPC methods."""
