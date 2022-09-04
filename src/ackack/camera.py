import asyncio
from tempfile import NamedTemporaryFile
import httpx
import rtsp
import cv2


class RTSPCam:
    """Call forgetful to get insights on current displaying images."""

    def __init__(self, rtsp_url, forgetful):
        self.client = rtsp.Client(rtsp_server_uri=rtsp_url)
        self.queue = asyncio.Queue()
        self._forgetful = forgetful

    async def __aenter__(self):
        self.client.open()
        return self

    async def __aexit__(self):
        self.client.close()

    def __aiter__(self):
        return self

    async def __anext__(self):
        async with httpx.AsyncClient() as client:
            img = self.client.read(raw=True)
            with NamedTemporaryFile('a+b', suffix=".jpg") as file:
                # TODO: Add support to forgetful (yoloair doesn't currently
                # support it, would need to be done too) to load numpy arrays
                # directly instead of image files
                cv2.imwrite(file.name, img)
                file.seek(0)
                resp = await client.post(self._forgetful,
                                         files={'face_image': file})
                print(resp)
                await asyncio.sleep(2)
                return resp
