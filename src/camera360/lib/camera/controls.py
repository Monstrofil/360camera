import typing

import pydantic


class BaseControl(pydantic.BaseModel):
    name: str

    value: typing.Any
    control_type: str

    description: str = ''


class MenuItem(BaseControl):
    options: list[str]

    control_type: typing.Literal["menu_item"] = "menu_item"


class Integer(BaseControl):
    value: int

    minimum: int = 10
    maximum: int = 20
    step: int = 1

    default: int = 5

    control_type: typing.Literal["integer"] = "integer"


AnyControl = typing.Union[MenuItem, Integer]


class ControlsModel(pydantic.BaseModel):
    controls: typing.List[typing.Union[MenuItem, Integer]] = pydantic.Field(
        ..., discriminator="control_type"
    )
