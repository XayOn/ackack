import os
from time import sleep
from pathlib import Path

from fastapi import FastAPI, Query, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from weback_unofficial.client import WebackApi
from weback_unofficial.vacuum import CleanRobot


def init_robot(user, pwd):
    client = WebackApi(user, pwd)
    client.get_session()
    return CustomRobot(client.device_list()[0]['Thing_Name'], client)


class CustomRobot(CleanRobot):
    def move_left(self):
        return self.publish_single('working_status', 'MoveLeft')

    def move_right(self):
        return self.publish_single('working_status', 'MoveRight')

    def move_up(self):
        return self.publish_single('working_status', 'MoveFront')

    def move_back(self):
        return self.publish_single('working_status', 'MoveBack')

    def move_down(self):
        return self.move_back()

    def move_stop(self):
        return self.publish_single('working_status', 'MoveStop')

    def move(self, position):
        getattr(self, f'move_{position}')()
        sleep(1)
        getattr(self, 'move_stop')()


BASE = os.getenv('BASE_URL', '')
RPRE = {'prefix': BASE} if os.getenv('BASE_URL') else {}
print(f"Starting with parameters {RPRE}")
router = APIRouter(**RPRE)

app = FastAPI()
app.mount(f"{BASE}/static", StaticFiles(directory="static"), name="main")
robot = init_robot(os.getenv('WEBACK_USERNAME'), os.getenv('WEBACK_PASSWORD'))


@router.get("/", response_class=HTMLResponse)
async def index():
    return Path('static/index.html').read_text()


@router.get("/move/")
async def calculate_recipes(movement: str = Query(None)):
    """Return recipes given a list of available alcohols"""
    if not movement:
        return []

    if movement not in ('stop', 'turn_on', 'turn_off'):
        robot.move(movement)
    else:
        getattr(robot, movement)()
    return {"status": "sent"}


app.include_router(router)
