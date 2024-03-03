from typing import List
from unittest import mock

from camera360.lib.rpc.decorators import MethodType
from camera360.lib.rpc.protocol import RPCProtocol, method


def test_protocol_subclass():
    class DemoProtocol(RPCProtocol):
        @method
        def init(self, arg1: str, arg2: List[str]) -> None:
            pass

        @method
        def finish(self) -> int: ...

        def not_a_method(self) -> int: ...

    assert DemoProtocol.methods == {
        "init": MethodType(args_model=mock.ANY, return_model=mock.ANY),
        "finish": MethodType(args_model=mock.ANY, return_model=mock.ANY),
    }

    assert DemoProtocol.methods["init"].args_model(
        arg1="argument1", arg2=["argument2"]
    ).model_dump() == dict(arg1="argument1", arg2=["argument2"])

    assert DemoProtocol.methods["init"].return_model(value=None).model_dump() == dict(
        value=None
    )

    assert DemoProtocol.methods["finish"].return_model(value=123).model_dump() == dict(
        value=123
    )
