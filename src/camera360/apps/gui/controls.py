from typing import Callable

from nicegui import ui

from camera360.lib.camera.controls import MenuItem, Integer, BaseControl


def menuoption(control: MenuItem, on_change=None) -> None:
    ui.label(control.name)
    combobox = ui.select(
        options=control.options, value=control.options[0], on_change=on_change
    )


def integer(control: Integer, on_change=None) -> None:
    ui.label(control.name)

    with ui.row():
        ui.label("Min = %s" % control.minimum)
        input = ui.number(
            value=30, min=control.minimum, max=control.maximum, on_change=on_change
        )
        ui.label("Max = %s" % control.maximum)


def create_control(control: BaseControl, on_change: Callable) -> None:
    callable = _type_to_control[control.control_type]

    with ui.card():
        callable(control, on_change=on_change)


_type_to_control = {"menu_item": menuoption, "integer": integer}
