from barcode_server.barcode import BarcodeReader
from barcode_server.config import AppConfig
from tests import TestBase


class BarcodeReaderTest(TestBase):

    async def test_initialization(self):
        config = AppConfig()
        reader = BarcodeReader(config)
        self.assertIsNotNone(reader)
