"""Custom ack robot."""
import asyncio
from loguru import logger
from .weback_api import WebackVacuumApi


class CustomRobot:
    """Extend  to allow movements"""

    def __init__(self):
        self.client = None
        self.thing = None
        self.status = None
        self.things = []

    async def login(self, user, pwd):
        region, user = user.split('-')
        self.client = WebackVacuumApi(user, pwd, region.replace('+', ''))
        if await self.client.login():
            self.things = await self.client.robot_list()
            await self.choose_thing()
            self.client.register_update_callback(self.cb_set_status)
        else:
            raise Exception('Could not login on weback')

    def cb_set_status(self, status):
        self.status = status

    async def send_command(self, payload, sync=False):
        """Send command."""
        await self.client.send_command(self.thing, payload, sync)

    async def set_status(self, status, **kwargs):
        """Set vacuum working status."""
        await self.client.set_status(self.thing, status, **kwargs)

    async def goto_command(self,  point: str):
        """Goto specific point."""
        await self.client.goto_command(self.thing, point)

    async def clean_rectangle_command(self, rect: str):
        """Clean rectangle."""
        await self.client.clean_rectangle_command(self.thing, rect)

    async def generic_command(self, command):
        """Generic command probably intended for internal WeBack use.

        Looks like these don't have a topic because they probably won't end
        up in an mqtt queue.
        """
        await self.client.generic_command(self.thing, command)

    async def update_status(self):
        """Request status update."""
        await self.generic_command('thing_status_get')

    async def choose_thing(self, thing_name=None):
        if not self.things:
            return False
        if not thing_name:
            thing_name = self.things[0]['thing_name']
        self.thing = next(
            iter([a for a in self.things if a['thing_name'] == thing_name]))
        self.thing['name'] = self.thing['thing_name']

    def stop(self):
        """Stop any current movement"""
        return self.set_status('MoveStop')

    async def move(self, pos):
        """Move for one second each pos"""
        logger.info(f'Moving to {pos}')
        if pos in ('left', 'right', 'front', 'back', 'stop'):
            await self.set_status(f'Move{pos.capitalize()}')
            await asyncio.sleep(1)
            return await self.set_status('Stop')
        logger.info(f'Getting default {pos}')
        await self.set_status(pos)
