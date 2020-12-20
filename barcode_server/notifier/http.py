import logging
from typing import List

import aiohttp
from prometheus_async.aio import time

from barcode_server.barcode import BarcodeEvent
from barcode_server.notifier import BarcodeNotifier
from barcode_server.stats import HTTP_NOTIFIER_TIME
from barcode_server.util import barcode_event_to_json

LOGGER = logging.getLogger(__name__)


class HttpNotifier(BarcodeNotifier):

    def __init__(self, method: str, url: str, headers: List[str]):
        super().__init__()
        self.method = method
        self.url = url
        headers = list(map(lambda x: tuple(x.split(':', 1)), headers))
        self.headers = list(map(lambda x: (x[0].strip(), x[1].strip()), headers))

    @time(HTTP_NOTIFIER_TIME)
    async def _send_event(self, event: BarcodeEvent):
        json = barcode_event_to_json(event)
        async with aiohttp.ClientSession() as session:
            async with session.request(self.method, self.url, headers=self.headers, data=json) as resp:
                resp.raise_for_status()
            LOGGER.debug(f"Notified {self.url}: {event.barcode}")
