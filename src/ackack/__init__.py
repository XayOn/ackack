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
    """Extend cleanrobot to allow movements"""

    def move_left(self):
        """Left"""
        return self.publish_single('working_status', 'MoveLeft')

    def move_right(self):
        """Right"""
        return self.publish_single('working_status', 'MoveRight')

    def move_up(self):
        """Up, actually front.

        This will move frontally, wich is the only non-rotating movement
        """
        return self.publish_single('working_status', 'MoveFront')

    def move_back(self):
        """Back, rotate 180 degrees"""
        return self.publish_single('working_status', 'MoveBack')

    def move_down(self):
        """Down key, back movement."""
        return self.move_back()

    def move_stop(self):
        """Stop any current movement"""
        return self.publish_single('working_status', 'MoveStop')

    def move(self, position):
        """Move for one second each position"""
        getattr(self, f'move_{position}')()
        sleep(1)
        getattr(self, 'move_stop')()


#: Setup BASE URL
BASE = os.getenv('BASE_URL', '')
RPRE = {'prefix': BASE} if os.getenv('BASE_URL') else {}
print(f"Starting with parameters {RPRE}")
router = APIRouter(**RPRE)

app = FastAPI()

# Distribute statics (vuejs app)
app.mount(f"{BASE}/static", StaticFiles(directory="static"), name="main")
robot = init_robot(os.getenv('WEBACK_USERNAME'), os.getenv('WEBACK_PASSWORD'))


@router.get("/", response_class=HTMLResponse)
async def index():
    return Path('static/index.html').read_text()


@router.get("/move/")
async def move(movement: str = Query(None)):
    """Move robot"""
    if not movement:
        return []

    if movement in ('left', 'right', 'up', 'down', 'back'):
        robot.move(movement)
    else:
        # Don't do the whole "move, wait 1s, stop moving" except on positional
        # movements
        getattr(robot, movement)()
    return {"status": "sent"}


app.include_router(router)
