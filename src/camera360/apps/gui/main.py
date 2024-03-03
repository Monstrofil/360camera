import base64
from typing import Optional

from nicegui import ui, app
from fastapi import Response

from camera360.apps.gui.controls import create_control
from camera360.lib.rpc.server import connect, Connection
from camera360.lib.supervisor.protocol import SupervisorProtocol, SystemStatus

supervisor: Optional[SupervisorProtocol] = None


async def handle_startup():
    global supervisor
    connection = Connection(host="127.0.0.1", port=8181)

    supervisor = await connection.connect(
        protocol=SupervisorProtocol, handler=None)
    print("Connected to %s" % supervisor)


app.on_startup(handle_startup)


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

    async def on_tick():
        nonlocal status
        new_status = await supervisor.status()
        status.__dict__.update(new_status.model_dump())

    ui.timer(0.5, on_tick)

    status = await supervisor.status()

    with ui.header().classes(replace="row items-center") as header, ui.tabs() as tabs:
        ui.tab("Main")

        for client in status.clients:
            ui.tab(client.name)

    with ui.tab_panels(tabs, value="Main").classes("w-full"):
        with ui.tab_panel("Main"):
            with ui.row():
                ui.label("Status:")
                ui.label().bind_text_from(status, "status")

                ui.spinner().bind_visibility_from(status, "pending_status")

            async def on_toggle_change(event):
                if event.value == "on":
                    await supervisor.start()
                elif event.value == "off":
                    await supervisor.stop()
                else:
                    raise NotImplementedError

            toggle_value = "on" if status.status == SystemStatus.capture else "off"
            ui.toggle(["on", "off"], value=toggle_value, on_change=on_toggle_change)

            with ui.card().classes("w-6/12") as card:
                video = ui.video(
                    src="#",
                    autoplay=True,
                    muted=True
                ).classes("w-full")
                ui.run_javascript(
                    f'attachHls({video.id}, "/video/stream/playlist.m3u8");'
                )

            ui.label("Controls")
            with ui.row():
                for item in await supervisor.controls():
                    create_control(control=item, on_change=lambda e: ui.notify(e.value))

        for client in status.clients:
            with ui.tab_panel(client.name):
                camera_tab_content()


@app.get("/video/stream/{rest_of_path:path}")
async def grab_video_frame(rest_of_path) -> Response:
    return Response(
        content=base64.decodebytes(await supervisor.preview(filename=rest_of_path)),
        media_type="text/plain",
    )


ui.run()
