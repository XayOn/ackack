import os
from time import sleep
import asyncio
from pathlib import Path
from loguru import logger

from fastapi import FastAPI, APIRouter, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .robot import CustomRobot
from .camera import RTSPCam

app = FastAPI()
CONFIG = {
    k[7:].lower(): v
    for k, v in os.environ.items() if k.startswith('ACKACK_')
}

#: Setup BASE URL
BASE = CONFIG.get('base', '')
router = APIRouter(**({'prefix': BASE} if BASE else {}))
app.mount(f"{BASE}/static", StaticFiles(directory="static"), name="main")

FFMPEG_CMD = ' '.join([
    "ffmpeg", "-hide_banner", "-loglevel", "fatal", '-rtsp_transport', 'tcp',
    '-flags', '-global_header', '-i', CONFIG["rtsp_uri"], '-an', '-c:v',
    'copy', '-b:v', '2048k', '-f', 'hls', '-lhls', '1', '-hls_time 1',
    '-hls_wrap', '5', '-hls_segment_type', 'fmp4',
    f"{Path('static').absolute()}/stream.m3u8"
])


async def forever_ffmpeg():
    while True:
        proc = await asyncio.create_subprocess_shell(' '.join(FFMPEG_CMD))
        logger.info(await proc.communicate())
        sleep(3)


@app.on_event('startup')
async def startup():
    """Setup robot and cam reading."""
    logger.info(f'Setting up weback ({CONFIG["user"]})')
    app.state.robot = CustomRobot.with_login(CONFIG['user'], CONFIG['pass'])
    logger.info(f'Setting up ffmpeg {FFMPEG_CMD}')
    app.state.ffmpeg = await asyncio.create_subprocess_shell(FFMPEG_CMD)
    logger.info(f'Setting up cam ({CONFIG["rtsp_uri"]})')
    app.state.cam = RTSPCam(CONFIG['rtsp_uri'], CONFIG.get('forgetful_uri'))
    await app.state.cam.__aenter__()


@router.get("/", response_class=HTMLResponse)
async def index():
    return Path('static/index.html').read_text().replace('BASE_', BASE or '')


async def send_data_from_cam(websocket):
    """If forgetful is enabled, send recognized objects via ws."""
    logger.info('starting send data from cam')
    if not CONFIG.get('forgetful'):
        return
    async for objects in app.state.cam:
        logger.info('received object in data from cam')
        logger.info(f'Sending detected objects ({objects}) to client')
        await websocket.send_json({'objects': objects.json()})


async def send_data_from_vacuum(websocket):
    """Request periodically vacuum status."""
    while True:
        app.state.robot.update()
        await websocket.send_json({
            'robot_state': {
                'state': app.state.robot.state,
                'mode': app.state.robot.current_mode
            }
        })
        await asyncio.sleep(3)


async def handle_movements(websocket):
    """Request robot movements to mqtt weback service."""
    logger.info('waiting for movements')
    while True:
        cmd = await websocket.receive_json()
        logger.info(f'received json {cmd}')
        await websocket.send_json(
            {"status": app.state.robot.move(cmd['action'])})


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    """Main websocket endpoint.

    Fires two coroutines: `handle_movements` and `send_data_from_cam`
    """
    logger.info('received ws request')
    await ws.accept()
    logger.info('starting coroutines')
    await asyncio.gather(handle_movements(ws), send_data_from_cam(ws),
                         send_data_from_vacuum(ws))


app.include_router(router)
