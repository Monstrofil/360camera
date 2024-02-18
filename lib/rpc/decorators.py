import inspect
import logging
from typing import TypeVar

import pydantic


def _init(cls):
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
        model = pydantic.create_model(name, **fields, __module__=cls.__name__)

        setattr(member, "model", model)


def _validate_method_args(argspec: inspect.FullArgSpec):
    if argspec.varkw is not None:
        raise ValueError("Keyword arguments are not supported: %s" % argspec.varkw)

    for arg in argspec.args:
        if arg == "self":
            continue

        if argspec.annotations.get(arg, None) is None:
            raise ValueError("Argument does not have proper annotation: %s" % arg)


T = TypeVar("T", bound=type)


def serializable(cls: type[T]) -> T:
    _init(cls)

    # save self-reference so everybody
    # can get original metadata
    cls.metadata = cls

    return cls
