import typing

import pydantic


class BaseControl(pydantic.BaseModel):
    name: str

    value: typing.Any
    control_type: str

    description: str = ''


class MenuItem(BaseControl):
    options: dict[int, str | int]

    control_type: typing.Literal["menu_item"] = "menu_item"


class NumericControl(BaseControl):
    value: int

    minimum: int = 10
    maximum: int = 20
    step: int = 1

    default: int = 5

    control_type: typing.Literal["integer"] = "integer"


class BooleanControl(NumericControl):
    minimum: int = 0
    maximum: int = 1

    default: int = 0

    control_type: typing.Literal["boolean"] = "boolean"


AnyControl = typing.Union[MenuItem, NumericControl, BooleanControl]


class ControlsModel(pydantic.BaseModel):
    controls: typing.List[typing.Union[MenuItem, NumericControl]] = pydantic.Field(
        ..., discriminator="control_type"
    )
