import asyncio
import logging
from typing import List

import aiohttp
from aiohttp import web
from aiohttp.web_middlewares import middleware
from prometheus_async.aio import time

from barcode_server.barcode import BarcodeReader, BarcodeEvent
from barcode_server.config import AppConfig
from barcode_server.const import *
from barcode_server.notifier import BarcodeNotifier
from barcode_server.notifier.http import HttpNotifier
from barcode_server.notifier.mqtt import MQTTNotifier
from barcode_server.notifier.ws import WebsocketNotifier
from barcode_server.stats import REST_TIME_DEVICES, WEBSOCKET_CLIENT_COUNT
from barcode_server.util import input_device_to_dict

LOGGER = logging.getLogger(__name__)
routes = web.RouteTableDef()


class Webserver:

    def __init__(self, config: AppConfig, barcode_reader: BarcodeReader):
        self.config = config
        self.host = config.SERVER_HOST.value
        self.port = config.SERVER_PORT.value

        self.clients = set()

        self.barcode_reader = barcode_reader
        self.barcode_reader.add_listener(self.on_barcode)

        self.notifiers: List[BarcodeNotifier] = []
        if config.HTTP_URL.value is not None:
            http_notifier = HttpNotifier(
                config.HTTP_METHOD.value,
                config.HTTP_URL.value,
                config.HTTP_HEADERS.value)
            self.notifiers.append(http_notifier)

        if config.MQTT_HOST.value is not None:
            mqtt_notifier = MQTTNotifier(
                host=config.MQTT_HOST.value,
                port=config.MQTT_PORT.value,
                client_id=config.MQTT_CLIENT_ID.value,
                user=config.MQTT_USER.value,
                password=config.MQTT_PASSWORD.value,
                topic=config.MQTT_TOPIC.value,
                qos=config.MQTT_QOS.value,
                retain=config.MQTT_RETAIN.value,
            )
            self.notifiers.append(mqtt_notifier)

    async def start(self):
        # start detecting and reading barcode scanners
        await self.barcode_reader.start()
        # start notifier queue processors
        for notifier in self.notifiers:
            await notifier.start()
        LOGGER.info(f"Starting webserver on {self.config.SERVER_HOST.value}:{self.config.SERVER_PORT.value} ...")

        app = self.create_app()
        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        site = aiohttp.web.TCPSite(
            runner,
            host=self.config.SERVER_HOST.value,
            port=self.config.SERVER_PORT.value
        )
        await site.start()

        # wait forever
        return await asyncio.Event().wait()

    def create_app(self) -> web.Application:
        app = web.Application(middlewares=[self.authentication_middleware])
        app.add_routes(routes)
        return app

    @middleware
    async def authentication_middleware(self, request, handler):
        if X_Auth_Token not in request.headers.keys() \
                or request.headers[X_Auth_Token] != self.config.SERVER_API_TOKEN.value:
            LOGGER.warning(f"Rejecting unauthorized connection: {request.host}")
            return web.HTTPUnauthorized()

        return await handler(self, request)

    @routes.get(f"/{ENDPOINT_DEVICES}")
    @time(REST_TIME_DEVICES)
    async def devices_handle(self, request):
        import orjson
        device_list = list(map(input_device_to_dict, self.barcode_reader.devices.values()))
        json = orjson.dumps(device_list)
        return web.Response(body=json, content_type="application/json")

    @routes.get("/")
    async def websocket_handler(self, request):
        websocket = web.WebSocketResponse()
        await websocket.prepare(request)

        self.clients.add(websocket)
        client_count = len(self.clients)
        WEBSOCKET_CLIENT_COUNT.set(client_count)

        notifier = WebsocketNotifier(websocket)
        await notifier.start()
        self.notifiers.append(notifier)

        LOGGER.debug(f"New client connected: {request.host} Client count: {client_count}")
        try:
            async for msg in websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    if msg.data.strip() == 'close':
                        await websocket.close()
                    else:
                        await websocket.send_str(msg.data + '/answer')
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    LOGGER.debug('ws connection closed with exception %s' %
                                 websocket.exception())
        except Exception as e:
            LOGGER.exception(e)
        finally:
            # TODO: this notifier should not be removed immediately, to provide queueing functionality
            self.notifiers.remove(notifier)
            await notifier.stop()

            self.clients.discard(websocket)
            client_count = len(self.clients)
            WEBSOCKET_CLIENT_COUNT.set(client_count)
            LOGGER.debug(f"Client disconnected: {request.host}")
        return websocket

    async def on_barcode(self, event: BarcodeEvent):
        for notifier in self.notifiers:
            await notifier.add_event(event)
