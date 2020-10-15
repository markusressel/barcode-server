import asyncio
import logging
from typing import List, Dict

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
        self.devices = {}
        self.listeners = set()

        self._main_task = None
        self._device_tasks = {}

    async def start(self):
        self._main_task = asyncio.create_task(self._detect_and_read())

    async def stop(self):
        if self._main_task is None:
            return

        for device_path, t in self._device_tasks.items():
            t.cancel()
        self._device_tasks.clear()
        self._main_task.cancel()
        self._main_task = None

    async def _detect_and_read(self):
        while True:
            try:
                self._detect_devices()

                for path, d in self.devices.items():
                    if path in self._device_tasks:
                        continue
                    LOGGER.info(
                        f"Reading: {d.path}: Name: {d.name}, "
                        f"Vendor: {d.info.vendor}, Product: {d.info.product}")
                    task = asyncio.create_task(self._start_reader(d))
                    self._device_tasks[path] = task

                await asyncio.sleep(1)
            except Exception as e:
                logging.exception(e)

    async def _start_reader(self, d):
        while True:
            try:
                barcode = await self._read_line(d)
                if barcode is not None:
                    SCAN_COUNT.inc()
                    LOGGER.debug(f"{d.name} ({d.path}): {barcode}")
                    for listener in self.listeners:
                        await listener(d, barcode)
            except Exception as e:
                LOGGER.exception(e)
                await asyncio.sleep(5)

    async def stop(self):
        self.running = False

    def _detect_devices(self):
        """
        Detects barcode USB devices
        """
        self.devices = self._find_devices(self.config.DEVICE_PATTERNS.value)

    @staticmethod
    def _find_devices(patterns: List) -> Dict[str, InputDevice]:
        """
        # Finds the input device with the name ".*Barcode Reader.*".
        # Could and should be parameterized, of course. Device name as cmd line parameter, perhaps?
        :param patterns: list of patterns to match the device name against
        :return: Map of ("Device Path" -> InputDevice) items
        """
        result = {}
        # find devices
        devices = evdev.list_devices()
        # create InputDevice instances
        devices = [evdev.InputDevice(fn) for fn in devices]

        # search for device name
        for d in devices:
            if any(map(lambda x: x.match(d.name), patterns)):
                result[d.path] = d

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
