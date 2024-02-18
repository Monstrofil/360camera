from typing import List

import pytest
from pydantic.fields import FieldInfo

from lib.rpc.decorators import serializable


@pytest.mark.xfail
def test_rpc_metadata():
    @serializable
    class Protocol:
        def init(self, arg1: str, arg2: List[str]) -> None:
            ...

    assert Protocol.metadata.init.model.model_fields == {
        'arg1': FieldInfo(annotation=str, required=True),
        'arg2': FieldInfo(annotation=List[str], required=True)}