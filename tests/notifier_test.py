from barcode_server.notifier.http import HttpNotifier
from tests import TestBase


class NotifierTest(TestBase):

    def test_http(self):
        method = "POST"
        url = "test.de"
        headers = []

        reader = HttpNotifier(method, url, headers)
        self.assertIsNotNone(reader)
