import typing

import pydantic


class BaseControl(pydantic.BaseModel):
    name: str

    control_type: str


class MenuItem(BaseControl):
    options: list[str]

    control_type: typing.Literal['menu_item'] = 'menu_item'


class Integer(BaseControl):
    minimum: int = 10
    maximum: int = 20

    default: int = 5

    control_type: typing.Literal['integer'] = 'integer'


AnyControl = typing.Union[MenuItem, Integer]


class ControlsModel(pydantic.BaseModel):
    controls: typing.List[typing.Union[MenuItem, Integer]] = \
        pydantic.Field(
            ..., discriminator='control_type')


