import inspect
import logging
import types
from dataclasses import dataclass
from typing import TypeVar, Union, Generic

import pydantic


@dataclass
class MethodType:
    args_model: type[pydantic.BaseModel]
    return_model: type[pydantic.BaseModel]
    streaming: bool


def _process(name: str, func: types.MethodType):
    logging.debug("Processing method %s", func)

    argspec = inspect.getfullargspec(func)
    _validate_method_args(argspec)

    fields = {
        argname: (argtype, ...)
        for argname, argtype in argspec.annotations.items()
        if argname != "return"
    }
    args_model = pydantic.create_model(
        name, **fields, __module__=func.__class__.__name__
    )

    return_type = argspec.annotations.get("return")
    if return_type is not None:
        if return_type.__name__ == "AsyncIterable":
            value_type = return_type.__args__[0]
            streaming = True
        else:
            value_type = return_type
            streaming = False

        return_model = pydantic.create_model(
            name,
            **{
                "value": (value_type, ...),
            },
            __module__=func.__class__.__name__,
        )
    else:
        return_model = None
        streaming = False

    model = MethodType(
        args_model=args_model, return_model=return_model, streaming=streaming
    )
    return model


def _init(prototype):
    metadata = dict()

    for name, member in inspect.getmembers(prototype):
        if not inspect.isfunction(member):
            continue

        if not getattr(member, "is_proto", False):
            continue

        metadata[name] = _process(name, member)
    return metadata


def _validate_method_args(argspec: inspect.FullArgSpec):
    if argspec.varkw is not None:
        raise ValueError("Keyword arguments are not supported: %s" % argspec.varkw)

    for arg in argspec.args:
        if arg == "self":
            continue

        if argspec.annotations.get(arg, None) is None:
            raise ValueError("Argument does not have proper annotation: %s" % arg)


T = TypeVar("T")


class SerializableMixin(Generic[T]):
    metadata: T


def serializable(cls: T) -> Union[T, SerializableMixin]:
    _init(cls)

    # save self-reference so everybody
    # can get original metadata
    cls.metadata = cls

    return cls
