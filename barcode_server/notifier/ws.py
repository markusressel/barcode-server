from prometheus_async.aio import time

from barcode_server.barcode import BarcodeEvent
from barcode_server.notifier import BarcodeNotifier
from barcode_server.stats import WEBSOCKET_NOTIFIER_TIME
from barcode_server.util import barcode_event_to_json


class WebsocketNotifier(BarcodeNotifier):

    def __init__(self, websocket):
        super().__init__()
        self.websocket = websocket

    @time(WEBSOCKET_NOTIFIER_TIME)
    async def _send_event(self, event: BarcodeEvent):
        json = barcode_event_to_json(self.config.INSTANCE_ID.value, event)
        await self.websocket.send_bytes(json)

        # TODO: can't log websocket address here because we don't have access
        #  to an unique identifier anymore, maybe we need to store one manually
        #  when the websocket is connected initially...
        # LOGGER.debug(f"Notified {client.remote_address}")
