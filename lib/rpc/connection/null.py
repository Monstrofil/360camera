import logging

from lib.camera.protocol import ProtocolHandler
from lib.rpc.connection import Connection


class LocalConnection(Connection):
    def __init__(self, handler: type[object]):
        super().__init__()
        self._handler = handler

    def communicate(self, method_name: str, arguments: bytes):
        logging.info("Sending request %s", arguments)

        # in regular sockets we will call all that network stuff
        return self.receive_message(method_name, arguments)

    def receive_message(self, method_name: str, arguments: bytes):
        mathod = getattr(self._handler, method_name)
        method_meta = getattr(self._handler.metadata, method_name)

        arguments = method_meta.model.parse_raw(arguments)
        return mathod(**arguments.dict())
