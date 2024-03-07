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
    ui.label(control.description)

    async def on_save():
        await on_change(input.value)

    with ui.row():
        input = ui.number(
            value=control.value,
            min=control.minimum,
            max=control.maximum,
            step=control.step
        )

        with ui.button(on_click=on_save).style('height: 100%') as btn:
            ui.icon('save')


def create_control(control: BaseControl, on_change: Callable) -> None:
    callable = _type_to_control[control.control_type]

    with ui.card().classes("w-4/12"):
        callable(control, on_change=on_change)


_type_to_control = {"menu_item": menuoption, "integer": integer}
