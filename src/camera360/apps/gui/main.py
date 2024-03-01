from typing import Optional

from nicegui import ui, app

from camera360.apps.gui.controls import create_control
from camera360.lib.rpc.server import connect
from camera360.lib.supervisor.protocol import SupervisorProtocol

supervisor: Optional[SupervisorProtocol] = None


async def handle_startup():
    global supervisor
    supervisor = await connect(
        host='127.0.0.1', port=8181,
        protocol=SupervisorProtocol,
        handler=None
    )
    print('Connected to %s' % supervisor)


app.on_startup(handle_startup)


def camera_tab_content():
    ui.label('Video stream')
    ui.video(src='//localhost').classes('w-6/12')
    ui.separator()

    ui.label('Controls')
    # with ui.row():
    #     for item in controls.controls:
    #         create_control(
    #             control=item,
    #             on_change=lambda e: ui.notify(e.value)
    #         )


@ui.page('/')
async def main():
    clients = await supervisor.get_clients()

    with ui.header().classes(replace='row items-center') as header, \
            ui.tabs() as tabs:
        ui.tab('Main')

        for client in clients:
            ui.tab(client.name)

    with ui.tab_panels(tabs, value='Main').classes('w-full'):
        with ui.tab_panel('Main'):
            ui.label('Content of Main')

            ui.label('Controls')
            with ui.row():
                for item in await supervisor.controls():
                    create_control(
                        control=item,
                        on_change=lambda e: ui.notify(e.value)
                    )

            async def on_toggle_change(event):
                if event.value == 'on':
                    await supervisor.start()
                elif event.value == 'off':
                    await supervisor.stop()
                else:
                    raise NotImplementedError
                print(event)

            ui.toggle(['on', 'off'], value='off', on_change=on_toggle_change)

        for client in clients:
            with ui.tab_panel(client.name):
                camera_tab_content()


ui.run()
