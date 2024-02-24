import pydantic
from pydantic import BaseModel


class MethodCall(BaseModel):
    method: str
    arguments: bytes

    type: str = "method_call"


class MethodReturn(pydantic.BaseModel):
    value: object
    type: str = "return"
