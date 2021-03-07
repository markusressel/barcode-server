import asyncio
import random
from unittest.mock import MagicMock

import aiohttp
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from barcode_server.barcode import BarcodeEvent
from barcode_server.util import barcode_event_to_json
from barcode_server.webserver import Webserver


def create_barcode_event_mock(barcode: str = None):
    device = lambda: None
    device.info = lambda: None
    device.name = "BARCODE SCANNER BARCODE SCANNER"
    device.path = "/dev/input/event3"
    device.info.vendor = 1
    device.info.product = 1

    event = BarcodeEvent(
        device,
        barcode if barcode is not None else f"{random.getrandbits(24)}"
    )

    return event


class WebsocketNotifierTest(AioHTTPTestCase):
    from barcode_server.config import AppConfig
    from container_app_conf.source.yaml_source import YamlSource

    # load config from test folder
    config = AppConfig(
        singleton=True,
        data_sources=[
            YamlSource("barcode_server", "./tests/")
        ]
    )

    webserver = None

    async def get_application(self):
        """
        Override the get_app method to return your application.
        """
        barcode_reader = MagicMock()
        self.webserver = Webserver(self.config, barcode_reader)
        app = self.webserver.create_app()
        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        site = aiohttp.web.TCPSite(
            runner,
            host=self.config.SERVER_HOST.value,
            port=self.config.SERVER_PORT.value
        )
        await site.start()
        return app

    # the unittest_run_loop decorator can be used in tandem with
    # the AioHTTPTestCase to simplify running
    # tests that are asynchronous
    @unittest_run_loop
    async def test_ws_connect_and_event(self):
        sample_event = create_barcode_event_mock("abcdefg")
        expected_json = barcode_event_to_json(sample_event)

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                    'http://127.0.0.1:9654/',
                    headers={"X-Auth-Token": self.config.SERVER_API_TOKEN.value}) as ws:
                asyncio.create_task(self.webserver.on_barcode(sample_event))
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.BINARY:
                        if expected_json == msg.data:
                            await ws.close()
                            assert True
                            return
                        else:
                            assert False
                    else:
                        assert False

        assert False
