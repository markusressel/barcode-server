import asyncio
import random
from unittest.mock import MagicMock

import aiohttp
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from barcode_server import const
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
        server_id = self.config.INSTANCE_ID.value
        expected_json = barcode_event_to_json(server_id, sample_event)

        import uuid
        client_id = str(uuid.uuid4())

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                    'http://127.0.0.1:9654/',
                    headers={
                        const.Client_Id: client_id,
                        const.X_Auth_Token: self.config.SERVER_API_TOKEN.value
                    }) as ws:
                asyncio.create_task(self.webserver.on_barcode(sample_event))
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.BINARY:
                        self.assertEqual(expected_json, msg.data)
                        await ws.close()
                        return
                    else:
                        self.fail("No event received")

        assert False

    @unittest_run_loop
    async def test_ws_reconnect_event_catchup(self):
        server_id = self.config.INSTANCE_ID.value
        missed_event = create_barcode_event_mock("abcdefg")
        second_event = create_barcode_event_mock("123456")
        missed_event_json = barcode_event_to_json(server_id, missed_event)
        second_event_json = barcode_event_to_json(server_id, second_event)

        import uuid
        client_id = str(uuid.uuid4())

        # connect to the server once
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                    'http://127.0.0.1:9654/',
                    headers={
                        const.Client_Id: client_id,
                        const.X_Auth_Token: self.config.SERVER_API_TOKEN.value
                    }) as ws:
                await ws.close()

        # then emulate a barcode scan event
        asyncio.create_task(self.webserver.on_barcode(missed_event))

        await asyncio.sleep(0.1)

        # and then reconnect again, expecting the event in between
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                    'http://127.0.0.1:9654/',
                    headers={
                        const.Client_Id: client_id,
                        const.X_Auth_Token: self.config.SERVER_API_TOKEN.value
                    }) as ws:
                # emulate another event, while connected
                asyncio.create_task(self.webserver.on_barcode(second_event))

                missed_event_received = False
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.BINARY:
                        if missed_event_json == msg.data:
                            if missed_event_received:
                                assert False
                            missed_event_received = True
                        elif second_event_json == msg.data:
                            if not missed_event_received:
                                assert False
                            await ws.close()
                            return
                        else:
                            assert False
                    else:
                        self.fail("No event received")

        assert False

    @unittest_run_loop
    async def test_ws_reconnect_drop_queue(self):
        server_id = self.config.INSTANCE_ID.value
        missed_event = create_barcode_event_mock("abcdefg")
        second_event = create_barcode_event_mock("123456")
        missed_event_json = barcode_event_to_json(server_id, missed_event)
        second_event_json = barcode_event_to_json(server_id, second_event)

        import uuid
        client_id = str(uuid.uuid4())

        # connect to the server once
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                    'http://127.0.0.1:9654/',
                    headers={
                        const.Client_Id: client_id,
                        const.X_Auth_Token: self.config.SERVER_API_TOKEN.value
                    }) as ws:
                await ws.close()

        # then emulate a barcode scan event while not connected
        asyncio.create_task(self.webserver.on_barcode(missed_event))

        await asyncio.sleep(0.1)

        # and then reconnect again, passing the "drop cache" header, expecting only
        # the new live event
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                    'http://127.0.0.1:9654/',
                    headers={
                        const.Client_Id: client_id,
                        const.Drop_Event_Queue: "",
                        const.X_Auth_Token: self.config.SERVER_API_TOKEN.value
                    }) as ws:
                # emulate another event, while connected
                asyncio.create_task(self.webserver.on_barcode(second_event))

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.BINARY:
                        if missed_event_json == msg.data:
                            self.fail("Received missed event despite queue drop")
                        elif second_event_json == msg.data:
                            await ws.close()
                            assert True
                            return
                        else:
                            self.fail("Received unexpected event")
                    else:
                        self.fail("No event received")

        assert False
