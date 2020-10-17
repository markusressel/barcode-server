import asyncio
import logging
from pathlib import Path
from typing import List, Dict

import evdev
from evdev import *

from barcode_server.config import AppConfig
from barcode_server.keyevent_reader import KeyEventReader
from barcode_server.stats import SCAN_COUNT

LOGGER = logging.getLogger(__name__)


class BarcodeReader:
    """
    Reads barcodes from a USB barcode scanner
    """

    def __init__(self, config: AppConfig):
        self.config = config
        self.devices = {}
        self.listeners = set()

        self._keyevent_reader = KeyEventReader()

        self._main_task = None
        self._device_tasks = {}

    async def start(self):
        """
        Start detecting and reading barcode scanner devices
        """
        self._main_task = asyncio.create_task(self._detect_and_read())

    async def stop(self):
        """
        Stop detecting and reading barcode scanner devices
        """
        if self._main_task is None:
            return

        for device_path, t in self._device_tasks.items():
            t.cancel()
        self._device_tasks.clear()
        self._main_task.cancel()
        self._main_task = None

    async def _detect_and_read(self):
        """
        Detect barcode scanner devices and start readers for them
        """
        while True:
            try:
                self._detect_devices()

                for path, d in self.devices.items():
                    if path in self._device_tasks:
                        continue
                    LOGGER.info(
                        f"Reading: {d.path}: Name: {d.name}, "
                        f"Vendor: {d.info.vendor:04x}, Product: {d.info.product:04x}")
                    task = asyncio.create_task(self._start_reader(d))
                    self._device_tasks[path] = task

                await asyncio.sleep(1)
            except Exception as e:
                logging.exception(e)
                await asyncio.sleep(10)

    async def _start_reader(self, input_device):
        """
        Start a reader for a specific device
        :param input_device: the input device
        """
        try:
            # become the sole recipient of all incoming input events
            input_device.grab()
            while True:
                barcode = await self._read_line(input_device)
                if barcode is not None and len(barcode) > 0:
                    asyncio.create_task(self._notify_listeners(input_device, barcode))
        except Exception as e:
            LOGGER.exception(e)
            self._device_tasks.pop(input_device.path)
        finally:
            try:
                # release device
                input_device.ungrab()
            except Exception as e:
                pass

    def _detect_devices(self):
        """
        Detects barcode USB devices
        """
        self.devices = self._find_devices(self.config.DEVICE_PATTERNS.value, self.config.DEVICE_PATHS.value)

    @staticmethod
    def _find_devices(patterns: List, paths: List[str]) -> Dict[str, InputDevice]:
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

        # filter by device name
        devices = list(filter(lambda d: any(map(lambda y: y.match(d.name), patterns)), devices))

        # add manually defined paths
        for path in paths:
            try:
                if Path(path).exists():
                    devices.append(evdev.InputDevice(path))
                else:
                    logging.warning(f"Path doesn't exist: {path}")
            except Exception as e:
                logging.exception(e)

        for d in devices:
            result[d.path] = d

        return result

    async def _read_line(self, input_device: InputDevice) -> str or None:
        """
        Read a single line (ENTER stops input) from the given device
        :param input_device: the device to listen on
        :return: a barcode
        """
        # Using a thread executor here is a workaround for
        # input_device.async_read_loop() skipping input events sometimes,
        # so we use a synchronous method instead.
        # While not perfect, it has a much higher success rate.
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._keyevent_reader.read_line, input_device)
        return result

    def add_listener(self, listener: callable):
        """
        Add a barcode event listener
        :param listener: async callable taking two arguments
        """
        self.listeners.add(listener)

    async def _notify_listeners(self, input_device: InputDevice, barcode: str):
        """
        Notifies all listeners about the scanned barcode
        :param input_device: device that scanned the barcode
        :param barcode: the barcode
        """
        SCAN_COUNT.inc()
        LOGGER.info(f"{input_device.name} ({input_device.path}): {barcode}")
        for listener in self.listeners:
            await listener(input_device, barcode)
