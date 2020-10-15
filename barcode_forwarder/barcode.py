import asyncio
import logging
from typing import List

import evdev
from evdev import *

from barcode_forwarder.config import AppConfig
from barcode_forwarder.stats import SCAN_COUNT

LOGGER = logging.getLogger(__name__)


class BarcodeReader:
    """
    Reads barcodes from a USB barcode scanner
    """

    running = False

    def __init__(self, config: AppConfig):
        self.config = config
        self.devices = []
        self.listeners = set()

    async def start(self):
        self.running = True
        while self.running:
            if len(self.devices) <= 0:
                self._detect_devices()
            if len(self.devices) <= 0:
                await asyncio.sleep(1)
                continue

            for d in self.devices:
                barcode = await self._read_line(d)
                if barcode is not None:
                    SCAN_COUNT.inc()
                    LOGGER.debug(f"{d.name} ({d.path}): {barcode}")
                    for listener in self.listeners:
                        await listener(d, barcode)

    async def stop(self):
        self.running = False

    def _detect_devices(self):
        """
        Detects barcode USB devices
        """
        self.devices = self._find_devices(self.config.DEVICE_PATTERNS.value)
        for device in self.devices:
            LOGGER.info(
                f"{device.path}: Name: {device.name}, Vendor: {device.info.vendor}, Product: {device.info.product}")

    @staticmethod
    def _find_devices(patterns: List) -> List[InputDevice]:
        """
        # Finds the input device with the name ".*Barcode Reader.*".
        # Could and should be parameterized, of course. Device name as cmd line parameter, perhaps?
        :param patterns: list of patterns to match the device name against
        :return: list of InputDevices
        """
        result = []
        # find devices
        devices = evdev.list_devices()
        # create InputDevice instances
        devices = [evdev.InputDevice(fn) for fn in devices]

        # search for device name
        for d in devices:
            if any(map(lambda x: x.match(d.name), patterns)):
                result.append(d)

        return result

    @staticmethod
    async def _read_line(input_device: InputDevice):
        """
        Read a single line (ENTER stops input) from the given device
        :param input_device: the device to listen on
        :return: a barcode
        """
        result = ""
        # read device events
        async for event in input_device.async_read_loop():
            if event.type == evdev.ecodes.EV_KEY and event.value == 1:
                keycode = categorize(event).keycode
                if keycode == 'KEY_ENTER':
                    # line is finished
                    return result
                else:
                    # append the current character
                    result += keycode[4:]

    def add_listener(self, listener: callable):
        """
        Add a barcode event listener
        :param listener: async callable taking two arguments
        """
        self.listeners.add(listener)
