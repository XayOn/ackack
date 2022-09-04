"""Custom ack robot."""
from weback_unofficial.client import WebackApi
from weback_unofficial.vacuum import CleanRobot
from time import sleep
from loguru import logger


class CustomRobot(CleanRobot):
    """Extend cleanrobot to allow movements"""

    @classmethod
    def with_login(cls, user, pwd):
        client = WebackApi(user, pwd)
        client.get_session()
        return cls(client.device_list()[0]['Thing_Name'], client)

    def stop(self):
        """Stop any current movement"""
        return self.publish_single('working_status', 'MoveStop')

    def move(self, pos):
        """Move for one second each pos"""
        logger.info(f'Moving to {pos}')
        if pos in ('left', 'right', 'front', 'back', 'stop'):
            self.publish_single('working_status', f'Move{pos.capitalize()}')
            sleep(1)
            logger.info(f'Stopping from {pos}')
            return self.stop()
        logger.info(f'Getting default {pos}')
        getattr(self, pos)()
