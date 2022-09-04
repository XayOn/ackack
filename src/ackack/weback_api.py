import asyncio
import websocket
import threading
import json
import logging
import hashlib
import httpx

_LOGGER = logging.getLogger(__name__)

AUTH_URL = "https://user.grit-cloud.com/prod/oauth"


class WebackVacuumApi:
    """Original work by agustin-e

    https://github.com/agustin-e/weback-home-assistant-component/
    """

    def __init__(self, user, password, region):
        _LOGGER.debug("WebackVacuumApi __init__")
        self.update_callback = self.null_callback
        self.user = user
        self.password = password
        self.region = region
        self.ws = None
        self.authorization = "Basic KG51bGwpOihudWxsKQ=="
        self.socket_state = "CLOSE"

    def register_update_callback(self, callback):
        """Register update callback."""
        self.update_callback = callback

    def null_callback(self, message):
        """Null callback, just log updates."""
        _LOGGER.debug("WebackVacuumApi null_callback: ", message)

    async def clone(self):
        """Return a cloned instance."""
        my_clone = self.__class__(
            self.user,
            self.password,
            self.region,
        )

        my_clone.jwt_token = self.jwt_token
        my_clone.region_name = self.region_name
        my_clone.wss_url = self.wss_url
        my_clone.api_url = self.api_url

        await my_clone.connect_wss()

        return my_clone

    async def login(self):
        """Login against remote API."""
        data = {
            "payload": {
                "opt": "login",
                "pwd": hashlib.md5(self.password.encode()).hexdigest()
            },
            "header": {
                "language": "es",
                "app_name": "WeBack",
                "calling_code": f"00{self.region}",
                "api_version": "1.0",
                "account": self.user,
                "client_id": "yugong_app"
            }
        }

        _LOGGER.debug(f"LOG URL: {AUTH_URL} ({data})")

        t = httpx.Timeout(30.0, connect=90.0)

        async with httpx.AsyncClient(timeout=t) as client:
            resp = (await client.post(AUTH_URL, json=data)).json()
            if resp['msg'] == 'success':
                data = resp['data']
                _LOGGER.debug(f"Token: {data['jwt_token']}")
                self.jwt_token = data['jwt_token']
                self.region_name = data['region_name']
                self.wss_url = data['wss_url']
                self.api_url = data['api_url']
                return True
            else:
                _LOGGER.error('WebackVacuumApi can\'t login (2) -'
                              ' verify user/password/region')

        await self.connect_wss()

    async def robot_list(self):
        """Mqtt-based calls require a destination, this one goes like this."""
        heads = {'Token': self.jwt_token, 'Region': self.region_name}
        async with httpx.AsyncClient() as client:
            res = await client.post(self.api_url,
                                    json=dict(opt='user_thing_list_get'),
                                    headers=heads)
            #: Trying to get json on a non-200 error will just break
            #: thus returning an exception to the user, wich, ironically
            #: seems more friendly than returning None
            if resp := res.json():
                if resp['msg'] != 'success':
                    raise Exception('Could not get thing list: {resp["msg"]}')
                _LOGGER.debug("Robots", resp['data']['thing_list'])
                return resp['data']['thing_list']

    async def connect_wss(self):
        """Connect to websocket server.

        Executed upon:

        - login
        - connection errors
        - cloning
        """
        _LOGGER.debug("WebackVacuumApi connect_wss")

        try:
            websocket.enableTrace(True)
            heads = {
                "Authorization": self.authorization,
                "region": self.region_name,
                "token": self.jwt_token,
                "Connection": "keep-alive, Upgrade",
                "handshakeTimeout": "10000"
            }
            self.ws = websocket.WebSocketApp(
                self.wss_url,
                header=heads,
                on_message=self.on_message,
                on_open=lambda _: setattr(self, 'socket_state', True),
                on_close=self.close_ws)

            self.wst = threading.Thread(target=self.ws.run_forever)
            self.wst.start()

            if self.wst.is_alive():
                _LOGGER.debug("> WssHandle thread iniciado OK")
            else:
                _LOGGER.debug("> WssHandle thread error al iniciar")

            for i in range(20):
                _LOGGER.debug(f"WSS waiting for connection ...{i}")
                if self.socket_state == "OPEN":
                    _LOGGER.debug("WSS conexión establecida")
                    return True
                await asyncio.sleep(0.5)

            _LOGGER.debug("WSS failed")
            return False

        except Exception as e:
            self.socket_state = "ERROR"
            _LOGGER.debug("Couldn't open socket", e)
            return False

    def close_ws(self):
        """Force stopping the run_forever running on another thread."""
        self.ws.close()

    def on_message(self, _, message):
        _LOGGER.debug("WebackVacuumApi recibe mensaje por socket", message)
        message = json.loads(message)
        if message["notify_info"] == "thing_status_update":
            self.update_callback(message["thing_status"])

    async def send_message_to_cloud(self, data, retries=3):
        for _ in range(retries):
            #: Events don't really matter here as we're only sending.
            #: Better to ask for forgiveness than permission, just retry it.
            try:
                self.ws.send(json.dumps(data))
            except (AttributeError,
                    websocket.WebSocketConnectionClosedException) as e:
                _LOGGER.error(f'Could not send message {data} to server: {e}')
                await self.connect_wss()
            else:
                return True

    async def send_command(self, thing, payload, sync=False):
        await self.send_message_to_cloud({
            "topic_name": f"$aws/things/{thing['name']}/shadow/update",
            "opt": "send_to_device",
            "sub_type": thing['sub_type'],
            "thing_name": thing['name'],
            "topic_payload": payload
        })
        if sync:
            await self._force_sync(thing)

    async def set_status(self, thing, status, **kwargs):
        """Set vacuum working status."""
        payload = {'state': {'working_status': status} | kwargs}
        await self.send_command(thing, payload, sync=True)

    async def goto_command(self, thing, point: str):
        """Goto specific point."""
        await self.set_status(thing, 'PlanningLocation', goto_point=point)

    async def clean_rectangle_command(self, thing, rect: str):
        """Clean rectangle."""
        await self.set_status(thing, 'PlanningRect', virtual_rect_info=rect)

    async def generic_command(self, thing, command):
        """Generic command probably intended for internal WeBack use.

        Looks like these don't have a topic because they probably won't end
        up in an mqtt queue.
        """
        await self.send_message_to_cloud({
            "opt": command,
            "sub_type": thing['sub_type'],
            "thing_name": thing['name']
        })

    async def update_status(self, thing):
        """Request status update."""
        await self.generic_command(thing, 'thing_status_get')

    async def _force_sync(self, thing):
        """Force sending commands to robot."""
        await self.generic_command(thing, "sync_thing")
