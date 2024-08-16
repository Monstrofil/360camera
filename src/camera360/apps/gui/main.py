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


async def generic_page_header():
    with ui.header().classes(replace="row items-center") \
            .classes('items-center duration-200 p-0 px-4 no-wrap') \
            .style('box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1)'):
        with ui.row():
            ui.link('Main', main_page).classes(replace='text-md text-white')
            ui.link('Preview', preview_page).classes(replace='text-md text-white')
            ui.link('Records', records_page).classes(replace='text-md text-white')
            ui.link('Advanced', advanced_page).classes(replace='text-md text-white')


@ui.page("/preview")
async def preview_page():
    await generic_page_header()
    ui.markdown("""
    **Preview**
    
    This section allows you to preview a video stream from your camera. 
    Aging your cameras and make sure that they are giving a proper video stream.
     
    During capture, this functionality is not available.
    """)

    controls_per_camera = await application.camera_controls()
    with ui.row():
        for camera_id in controls_per_camera.keys():
            with ui.card():
                img = ui.image('/preview.jpeg?camera_id=%s' % camera_id).classes('w-64')
                ui.button('Force reload', on_click=img.force_reload)
                ui.label('Camera preview %s' % camera_id)


@ui.page("/records")
async def records_page():
    await generic_page_header()
    ui.markdown("""
    **Records**

    This section allows you to view existing records.
    """)

    captures = await application.captures()
    with ui.row():
        for capture in captures:
            with ui.card():
                ui.label('Camera capture %s' % capture)


@ui.page("/advanced")
async def advanced_page():
    await generic_page_header()
    ui.markdown("""
        **Advanced settings**

        This section allows you to fine-tune your camera settings using advanced settings.
        You must have a deep knowledge in camera settings before you can use advanced settings.
        """)

    async def on_camera_control_change(camera_id: str, control: AnyControl, value: Any):
        ui.notify("Camera control changed: %s" % value)
        await application.set_camera_control(camera_id, control.name, value)

    controls_per_camera = await application.camera_controls()
    tabs_per_camera = []
    with ui.tabs().classes('w-full') as tabs:
        for camera_id, camera_ctrls in controls_per_camera.items():
            tabs_per_camera.append(ui.tab(camera_id))

    with ui.tab_panels(tabs, value="Camera controls").classes('w-full'):
        for tab, (camera_id, camera_ctrls) in zip(tabs_per_camera, controls_per_camera.items()):
            with ui.tab_panel(tab), ui.row().classes('w-full'):
                for item in camera_ctrls:
                    create_control(
                        control=item,
                        on_change=partial(on_camera_control_change, camera_id, item))


@ui.page("/")
async def main_page():
    status = await application.status()

    await generic_page_header()

    with ui.row():
        ui.label("Status:")
        ui.label().bind_text_from(status, "status")

        ui.spinner().bind_visibility_from(status, "pending_status")

    async def on_toggle_change(event):
        try:
            if event.value == "on":
                await application.start_capture()
            elif event.value == "off":
                await application.stop_capture()
            else:
                raise NotImplementedError
        except Exception as e:
            ui.notify(str(e), type='negative')
            await application.status(refresh=True)

    toggle_value = "on" if status.status == SystemStatus.capture else "off"
    ui.toggle(["on", "off"], value=toggle_value, on_change=on_toggle_change)

    async def on_control_change(control: AnyControl, value: Any):
        ui.notify(value)

        await application.set_control(control.name, value)

    ui.label("Controls")
    with ui.row().classes('w-full'):
        for item in await application.controls():
            create_control(control=item, on_change=partial(on_control_change, item))


@app.get("/preview.jpeg")
async def preview_image(camera_id: str) -> Response:
    base64_image = await application.get_camera_preview(camera_id=camera_id)
    return Response(
        content=base64.decodebytes(base64_image),
        media_type="media/jpeg",
    )


def main():
    ui.run()


if __name__ in {"__main__", "__mp_main__"}:
    main()
