

class SignalRpcException(Exception):
    message: str
    body: dict
    def __init__(self, message: str, body: dict):
        self.message = message
        self.body = body
