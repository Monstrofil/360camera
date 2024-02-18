from typing import AsyncGenerator

import pydantic
from pydantic import BaseModel


class RPCRequest(BaseModel):
    method: str
    arguments: bytes

    type: str = "method_call"


class RPCResponse(pydantic.BaseModel):
    value: object
    type: str = "return"


class Connection:
    def __init__(self):
        pass

    async def stream(
        self, method_name: str, arguments: bytes
    ) -> AsyncGenerator[RPCResponse, None]:
        ...

    async def receive_message(self, method_name: str, arguments: bytes):
        ...
