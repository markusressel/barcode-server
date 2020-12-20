from datetime import datetime
from unittest.mock import Mock

from barcode_server.barcode import BarcodeEvent
from barcode_server.util import barcode_event_to_json
from tests import TestBase


class ApiTest(TestBase):

    def test_json(self):
        date_str = "2020-08-03T10:00:00+00:00"

        input_device = Mock()
        input_device.name = "Barcode Scanner"
        input_device.path = "/dev/input/event2"
        input_device.info.vendor = 1
        input_device.info.product = 2

        # {
        #     "name": input_device.name,
        #     "path": input_device.path,
        #     "vendorId": f"{input_device.info.vendor: 04x}",
        #     "productId": f"{input_device.info.product: 04x}",
        # }
        date = datetime.fromisoformat(str(date_str))
        barcode = "4006824000970"

        event = BarcodeEvent(input_device, barcode, date)
        event_json = str(barcode_event_to_json(event))

        self.assertIn(date_str, event_json)
        self.assertIn(input_device.path, event_json)
        self.assertIn(barcode, event_json)
        self.assertIsNotNone(event_json)
