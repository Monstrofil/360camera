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


def _process_method(model_name: str, func: types.MethodType):
    logging.debug("Processing method %s", func)

    argspec = inspect.getfullargspec(func)
    _validate_method_args(argspec)

    fields = {
        argname: (argtype, ...)
        for argname, argtype in argspec.annotations.items()
        if argname != "return"
    }
    args_model = pydantic.create_model(
        model_name, **fields, __module__=str(func.__class__.__name__)
    )

    return_type = argspec.annotations.get("return")

    # special case when method returns None
    # pydantic needs type(None) which is NoneType
    if return_type is None:
        return_type = types.NoneType

    return_model = pydantic.create_model(
        model_name,
        **{
            "value": (return_type, ...),
        },
        __module__=str(func.__class__.__name__),
    )

    model = MethodType(
        args_model=args_model,
        return_model=return_model,
    )
    return model


def _init(prototype):
    metadata = dict()

    is_rpc_method = lambda member: inspect.isfunction(member) and getattr(
        member, "is_proto", False
    )

    for name, method in inspect.getmembers(prototype, predicate=is_rpc_method):
        metadata[name] = _process_method(name, method)
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
