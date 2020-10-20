import logging
from typing import List

import aiohttp
from evdev import InputDevice

from barcode_server.notifier import BarcodeNotifier
from barcode_server.util import barcode_event_to_json

LOGGER = logging.getLogger(__name__)


class HttpNotifier(BarcodeNotifier):

    def __init__(self, method: str, url: str, headers: List[str]):
        self.method = method
        self.url = url
        self.headers = headers

    async def notify(self, device: InputDevice, barcode: str):
        json = barcode_event_to_json(device, barcode)
        async with aiohttp.ClientSession() as session:
            try:
                await session.request(self.method, self.url, headers=self.headers, data=json)
            except Exception as e:
                LOGGER.exception(e)
