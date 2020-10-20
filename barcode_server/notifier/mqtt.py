import logging

from asyncio_mqtt import Client
from evdev import InputDevice

from barcode_server.notifier import BarcodeNotifier
from barcode_server.util import barcode_event_to_json

LOGGER = logging.getLogger(__name__)


class MQTTNotifier(BarcodeNotifier):

    def __init__(self, host: str, port: int = 1883,
                 topic: str = "/barcode-server/barcode",
                 client_id: str = "barcode-server",
                 user: str = None, password: str = None,
                 qos: int = 2, retain: bool = False):
        self.client_id = client_id
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.topic = topic
        self.qos = qos
        self.retain = retain

    async def notify(self, device: InputDevice, barcode: str):
        json = barcode_event_to_json(device, barcode)
        try:
            async with Client(hostname=self.host, port=self.port,
                              username=self.user, password=self.password,
                              client_id=self.client_id) as client:
                await client.publish(self.topic, json, self.qos, self.retain)
                LOGGER.debug(f"Notified {self.host}:{self.port}: {barcode}")
        except Exception as e:
            LOGGER.exception(e)
