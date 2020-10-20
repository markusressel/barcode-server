from evdev import InputDevice


class BarcodeNotifier:

    async def notify(self, device: InputDevice, barcode: str):
        """
        Called when a new barcode has been scanned and clients must be notified.
        :param device: the device that scanned the barcode
        :param barcode: the barcode
        """
        raise NotImplementedError()
