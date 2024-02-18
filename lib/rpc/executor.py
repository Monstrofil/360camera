import inspect
import logging
from functools import partial


from lib.camera.protocol import ServerProtocol, MethodType
from lib.rpc.connection import Connection


class Executor:
    def __init__(self, protocol: type[ServerProtocol], connection: Connection):
        self._protocol = protocol
        self._connection = connection

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

        stream = await self._connection.stream(
            method_name, payload.model_dump_json().encode()
        )

        if member.streaming:
            return (
                member.return_model(**response.dict()).value
                async for response in stream
            )
        else:
            if member.return_model is None:
                return None

            async for item in stream:
                return member.return_model(**item.dict()).value
