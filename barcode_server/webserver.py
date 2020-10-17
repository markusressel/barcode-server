import logging
from http import HTTPStatus
from typing import Dict, Optional, Callable, Awaitable, Any

import orjson
import websockets
from evdev import InputDevice
from websockets import WebSocketServerProtocol, WebSocketServer
from websockets.http import Headers
from websockets.server import HTTPResponse

from barcode_server.barcode import BarcodeReader
from barcode_server.config import AppConfig
from barcode_server.const import X_Auth_Token

LOGGER = logging.getLogger(__name__)


class CustomProtocol(WebSocketServerProtocol):

    def __init__(self, ws_handler: Callable[["WebSocketServerProtocol", str], Awaitable[Any]],
                 ws_server: "WebSocketServer", **kwargs: Any):
        super().__init__(ws_handler, ws_server, **kwargs)

    def process_request(
            self, path: str, request_headers: Headers
    ) -> Optional[HTTPResponse]:
        config = AppConfig()
        if X_Auth_Token not in request_headers.keys() \
                or request_headers[X_Auth_Token] != config.SERVER_API_TOKEN.value:
            LOGGER.warning(f"Rejecting unauthorized connection: {self.remote_address[0]}:{self.remote_address[1]}")
            return HTTPStatus.UNAUTHORIZED, request_headers


class Webserver:

    def __init__(self, config: AppConfig, barcode_reader: BarcodeReader):
        self.config = config
        self.host = config.SERVER_HOST.value
        self.port = config.SERVER_PORT.value

        self.clients = set()

        self.barcode_reader = barcode_reader
        self.barcode_reader.add_listener(self.on_barcode)

    async def start(self):
        await self.barcode_reader.start()
        LOGGER.info("Starting webserver...")
        return await websockets.serve(self.connection_handler, self.host, self.port,
                                      create_protocol=CustomProtocol)

    async def connection_handler(self, websocket, path):
        self.clients.add(websocket)
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
            LOGGER.debug(f"Client disconnected: {websocket.remote_address}")

    async def on_barcode(self, device: InputDevice, barcode: str):
        for client in self.clients:
            event = {
                "device": {
                    "name": device.name,
                    "path": device.path,
                    "vendorId": f"{device.info.vendor: 04x}",
                    "productId": f"{device.info.product: 04x}",
                },
                "barcode": barcode
            }
            json = orjson.dumps(event)
            await client.send(json)
