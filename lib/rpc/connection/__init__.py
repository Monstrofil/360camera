class Connection:
    def __init__(self):
        pass

    def communicate(self, method_name: str, arguments: bytes):
        ...

    def receive_message(self, method_name: str, arguments: bytes):
        ...
