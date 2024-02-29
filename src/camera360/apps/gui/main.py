from typing import Optional

from nicegui import ui, app

from camera360.apps.gui.controls import create_control
from camera360.lib.camera.controls import ControlsModel, MenuItem, Integer
from camera360.lib.rpc.server import connect
from camera360.lib.supervisor.protocol import SupervisorProtocol

executor: Optional[SupervisorProtocol] = None


async def handle_startup():
    global executor
    executor = await connect(
        host='127.0.0.1', port=8181,
        protocol=SupervisorProtocol,
        handler=None
    )
    print('Connected to %s' % executor)


app.on_startup(handle_startup)


controls = ControlsModel(controls=(
    MenuItem(name='Test patterns', options=['Vertical Bars', 'Horizontal', 'c'], control_type='menu_item'),
    Integer(name='Frequency', minimum=10, maximum=25, default=1),
    Integer(name='Exposure', minimum=10, maximum=25, default=1),
    Integer(name='Vertical Bars', minimum=10, maximum=25, default=1)
))


#
# with ui.footer(value=False) as footer:
#     ui.label('Footer')
#
# with ui.left_drawer().classes('bg-blue-100') as left_drawer:
#     ui.label('Side menu')
#
# with ui.page_sticky(position='bottom-right', x_offset=20, y_offset=20):
#     ui.button(
#         on_click=footer.toggle, icon='contact_support'
#     ).props('fab')
#

#
#
def camera_tab_content():
    ui.label('Video stream')
    ui.video(src='//localhost').classes('w-6/12')
    ui.separator()

    ui.label('Controls')
    with ui.row():
        for item in controls.controls:
            create_control(
                control=item,
                on_change=lambda e: ui.notify(e.value)
            )


@ui.page('/')
async def main():
    clients = await executor.get_clients()

    with ui.header().classes(replace='row items-center') as header, \
            ui.tabs() as tabs:
        ui.tab('Main')

        for client in clients:
            ui.tab(client.name)

    with ui.tab_panels(tabs, value='Main').classes('w-full'):
        with ui.tab_panel('Main'):
            ui.label('Content of Main')

            async def on_toggle_change(event):
                if event.value == 'on':
                    await executor.start()
                elif event.value == 'off':
                    await executor.stop()
                else:
                    raise NotImplementedError
                print(event)

            ui.toggle(['on', 'off'], value='off', on_change=on_toggle_change)

        for client in clients:
            with ui.tab_panel(client.name):
                camera_tab_content()


ui.run()
