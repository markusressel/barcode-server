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
        headers = list(map(lambda x: tuple(x.split(':', 1)), headers))
        self.headers = list(map(lambda x: (x[0].strip(), x[1].strip()), headers))

    async def notify(self, device: InputDevice, barcode: str):
        json = barcode_event_to_json(device, barcode)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(self.method, self.url, headers=self.headers, data=json) as resp:
                    resp.raise_for_status()
                LOGGER.debug(f"Notified {self.url}: {barcode}")
        except Exception as e:
            LOGGER.exception(e)
