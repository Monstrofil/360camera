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
    ui.add_body_html(
        '<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>'
    )
    ui.add_body_html("""<script>
        function attachHls(element, source) {
          var video = document.getElementById('c' + element);
          if(Hls.isSupported()) {
            var hls = new Hls();
            hls.loadSource('/video/stream/preview.m3u8');
            hls.attachMedia(video);
            hls.on(Hls.Events.MANIFEST_PARSED,function() {
                video.play();
            });
          }
        }</script>""")

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

            with ui.card().classes("w-3/12") as card:
                video = ui.video(
                    src="#",
                    autoplay=True,
                    muted=True
                ).classes("w-full")
                ui.run_javascript(
                    f'attachHls({video.id}, "/video/stream/playlist.m3u8");'
                )

            async def on_control_change(control: AnyControl, value: Any):
                ui.notify(value)

                await application.set_control(control.name, value)

            ui.label("Controls")
            with ui.row().classes('w-full'):
                for item in await application.controls():
                    create_control(control=item, on_change=partial(on_control_change, item))

        # for client in status.clients:
        #     with ui.tab_panel(client.name):
        #         camera_tab_content()


@app.get("/video/stream/{rest_of_path:path}")
async def grab_video_frame(rest_of_path) -> Response:
    return Response(
        content=base64.decodebytes(await application.preview(filename=rest_of_path)),
        media_type="text/plain",
    )


ui.run()
