import logging
from typing import Dict

import orjson
import websockets
from evdev import InputDevice

from barcode_forwarder.barcode import BarcodeReader
from barcode_forwarder.config import AppConfig

LOGGER = logging.getLogger(__name__)


class Webserver:

    def __init__(self, config: AppConfig, barcode_reader: BarcodeReader):
        self.config = config
        self.host = config.SERVER_HOST.value
        self.port = config.SERVER_PORT.value

        self.clients = set()
        self.login_map: Dict[
            websockets.WebSocketServerProtocol, str or None] = {}  # used to keep track of logged in user
        self.subscriptions = {}

        self.barcode_reader = barcode_reader
        self.barcode_reader.add_listener(self.on_barcode)

    async def start(self):
        LOGGER.info("Starting webserver...")
        return await websockets.serve(self.connection_handler, self.host, self.port)

    async def connection_handler(self, websocket, path):
        self.clients.add(websocket)
        self.login_map[websocket] = None
        LOGGER.debug(f"New client connected: {websocket.remote_address} Client count: {len(self.clients)}")
        try:
            while True:
                request_message = await websocket.recv()
        except websockets.ConnectionClosedOK:
            pass
        except Exception as e:
            LOGGER.exception(e)
        finally:
            self.clients.remove(websocket)
            self.login_map.pop(websocket)
            LOGGER.debug(f"Client disconnected: {websocket.remote_address}")

    async def on_barcode(self, device: InputDevice, barcode: str):
        for client in self.clients:
            event = {
                "device": {
                    "name": device.name,
                    "path": device.path,
                    "vendorId": device.info.vendor,
                    "productId": device.info.product,
                },
                "barcode": barcode
            }
            json = orjson.dumps(event)
            await client.send(json)
