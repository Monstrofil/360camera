import inspect
import logging
from functools import partial


from lib.camera.protocol import ServerProtocol, MethodType
from lib.rpc.connection.channel import Channel, Iterator
from lib.rpc.connection import MethodCall


class Executor:
    def __init__(self, protocol: type[ServerProtocol], channel: Channel):
        self._protocol = protocol
        self._channel = channel

        for name, member in inspect.getmembers(self._protocol):
            if not inspect.isfunction(member):
                continue

            logging.debug("Processing method %s", member)

            # copying methods from the protocol but overriding them with remote call logic
            self.__dict__[name] = partial(self._call_remote_method, member, name)

    async def _call_remote_method(
        self,
        member: MethodType,
        method_name: str,
        **arguments,
    ):
        payload = member.args_model(**arguments)
        response = await self._channel.send_request(
            MethodCall(method=method_name, arguments=payload.model_dump_json().encode())
            .model_dump_json()
            .encode()
            + b"\n"
        )

        if member.return_model is None:
            return None

        if isinstance(response, Iterator):
            return (
                member.return_model.parse_raw(item).value async for item in response
            )
        return member.return_model.parse_raw(response).value
