import base64
from functools import partial
from typing import Optional, Any

from nicegui import ui, app
from fastapi import Response

from camera360.apps.gui.app import Application
from camera360.apps.gui.controls import create_control
from camera360.lib.camera.controls import AnyControl
from camera360.lib.supervisor.protocol import SystemStatus

application: Optional[Application] = None


async def handle_startup():
    global application
    application = Application()

    await application.connect()


app.on_startup(handle_startup)


# async def handle_shutdown():
#     await application.disconnect()
#
#
# app.on_shutdown(handle_shutdown)


def camera_tab_content():
    ui.label("Video stream")
    ui.video(src="//localhost", autoplay=True, muted=True).classes("w-6/12")
    ui.separator()

    ui.label("Controls")
    # with ui.row():
    #     for item in controls.controls:
    #         create_control(
    #             control=item,
    #             on_change=lambda e: ui.notify(e.value)
    #         )


@ui.page("/")
async def main():
    status = await application.status()

    with ui.header().classes(replace="row items-center") as header, ui.tabs() as tabs:
        ui.tab("Main")

        # for client in status.clients:
        #     ui.tab(client.name)

    with ui.tab_panels(tabs, value="Main").classes("w-full"):
        with ui.tab_panel("Main"):
            with ui.row():
                ui.label("Status:")
                ui.label().bind_text_from(status, "status")

                ui.spinner().bind_visibility_from(status, "pending_status")

            async def on_toggle_change(event):
                if event.value == "on":
                    await application.start_capture()
                elif event.value == "off":
                    await application.stop_capture()
                else:
                    raise NotImplementedError

            toggle_value = "on" if status.status == SystemStatus.capture else "off"
            ui.toggle(["on", "off"], value=toggle_value, on_change=on_toggle_change)

            async def on_control_change(control: AnyControl, value: Any):
                ui.notify(value)

                await application.set_control(control.name, value)

            async def on_camera_control_change(camera_id: str, control: AnyControl, value: Any):
                ui.notify("Camera control changed: %s" % value)
                await application.set_camera_control(camera_id, control.name, value)

            ui.label("Controls")
            with ui.row().classes('w-full'):
                for item in await application.controls():
                    create_control(control=item, on_change=partial(on_control_change, item))

            controls_per_camera = await application.camera_controls()
            ui.label("Preview")
            with ui.row():
                for camera_id in controls_per_camera.keys():
                    with ui.card():
                        img = ui.image('/preview.jpeg?camera_id=%s' % camera_id).classes('w-64')
                        ui.button('Force reload', on_click=img.force_reload)
                        ui.label('Camera preview %s' % camera_id)

            ui.label("Cameras controls")
            tabs_per_camera = []
            with ui.tabs().classes('w-full') as tabs:
                ui.tab("Camera controls")
                for camera_id, camera_ctrls in controls_per_camera.items():
                    tabs_per_camera.append(ui.tab(camera_id))

            with ui.tab_panels(tabs, value="Camera controls").classes('w-full'):
                with ui.tab_panel("Camera controls"):
                    ui.markdown("### Controls for cameras")

                for tab, (camera_id, camera_ctrls) in zip(tabs_per_camera, controls_per_camera.items()):
                    with ui.tab_panel(tab), ui.row().classes('w-full'):
                        for item in camera_ctrls:
                            create_control(
                                control=item,
                                on_change=partial(on_camera_control_change, camera_id, item))


        # for client in status.clients:
        #     with ui.tab_panel(client.name):
        #         camera_tab_content()


@app.get("/video/stream/{rest_of_path:path}")
async def grab_video_frame(rest_of_path) -> Response:
    return Response(
        content=base64.decodebytes(await application.preview(filename=rest_of_path)),
        media_type="text/plain",
    )


@app.get("/preview.jpeg")
async def preview_image(camera_id: str) -> Response:
    base64_image = await application.get_camera_preview(camera_id=camera_id)
    return Response(
        content=base64.decodebytes(base64_image),
        media_type="media/jpeg",
    )


ui.run()
