from barcode_forwarder.barcode import BarcodeReader
from barcode_forwarder.config import AppConfig
from tests import TestBase


class ProductManagerTest(TestBase):

    def test_initialization(self):
        config = AppConfig()
        reader = BarcodeReader(config)
        self.assertIsNotNone(reader)
