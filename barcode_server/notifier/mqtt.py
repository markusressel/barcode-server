import logging

from aiomqtt import Client
from prometheus_async.aio import time

from barcode_server.barcode import BarcodeEvent
from barcode_server.notifier import BarcodeNotifier
from barcode_server.stats import MQTT_NOTIFIER_TIME
from barcode_server.util import barcode_event_to_json

LOGGER = logging.getLogger(__name__)


class MQTTNotifier(BarcodeNotifier):

    def __init__(self, host: str, port: int = 1883,
                 topic: str = "/barcode-server/barcode",
                 client_id: str = "barcode-server",
                 user: str = None, password: str = None,
                 qos: int = 2, retain: bool = False):
        super().__init__()
        self.client_id = client_id
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.topic = topic
        self.qos = qos
        self.retain = retain

    @time(MQTT_NOTIFIER_TIME)
    async def _send_event(self, event: BarcodeEvent):
        json = barcode_event_to_json(self.config.INSTANCE_ID.value, event)
        async with Client(hostname=self.host, port=self.port,
                          username=self.user, password=self.password,
                          identifier=self.client_id) as client:
            await client.publish(self.topic, json, self.qos, self.retain)
            LOGGER.debug(f"Notified {self.host}:{self.port}: {event.barcode}")
