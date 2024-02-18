import inspect
import logging
from functools import partial

import pydantic

from lib.camera.protocol import ServerProtocol
from lib.rpc.connection import Connection


class Executor:
    def __init__(self, protocol: type[ServerProtocol], connection: Connection):
        self._protocol = protocol
        self._connection = connection

        for name, member in inspect.getmembers(self._protocol):
            if not inspect.isfunction(member):
                continue

            logging.debug("Processing method %s", member)
            self.__dict__[name] = partial(self._call_remote_method, member.model, name)

    def _call_remote_method(
        self, model: type[pydantic.BaseModel], method_name: str, **arguments
    ):
        payload = model(**arguments)
        return self._connection.communicate(method_name, payload.json().encode())
