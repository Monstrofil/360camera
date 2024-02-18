import inspect
import logging
from typing import TypeVar, Union, Generic

import pydantic


def _init(cls):
    cls.registered = {}

    for name, member in inspect.getmembers(cls):
        if not inspect.isfunction(member):
            continue

        logging.debug("Processing method %s", member)

        argspec = inspect.getfullargspec(member)
        _validate_method_args(argspec)

        fields = {
            argname: (argtype, ...)
            for argname, argtype in argspec.annotations.items()
            if argname != "return"
        }
        args_model = pydantic.create_model(name, **fields, __module__=cls.__name__)

        return_type = argspec.annotations.get("return")
        if return_type is not None:
            return_model = pydantic.create_model(
                name, **{"value": (return_type, ...)}, __module__=cls.__name__
            )
        else:
            return_model = None

        setattr(member, "args_model", args_model)
        setattr(member, "return_model", return_model)
        cls.registered[name] = member


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
