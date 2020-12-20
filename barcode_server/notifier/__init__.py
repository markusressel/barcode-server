import asyncio
import logging
from asyncio import Task

from barcode_server.barcode import BarcodeEvent

LOGGER = logging.getLogger(__name__)


class BarcodeNotifier:
    """
    Base class for a notifier.
    """

    def __init__(self):
        self.event_queue = asyncio.Queue()
        self.processor_task: Task = None

    async def start(self):
        """
        Starts the event processor of this notifier
        """
        self.processor_task = asyncio.create_task(self.event_processor())

    async def stop(self):
        """
        Stops the event processor of this notifier
        """
        if self.processor_task is None:
            return

        self.processor_task.cancel()
        self.processor_task = None

    async def event_processor(self):
        """
        Processes the event queue
        """
        while True:
            try:
                event = await self.event_queue.get()

                success = False
                while not success:
                    try:
                        await self._send_event(event)
                        success = True
                    except Exception as ex:
                        LOGGER.exception(ex)
                        await asyncio.sleep(2)

            except Exception as ex:
                LOGGER.exception(ex)

    async def add_event(self, event: BarcodeEvent):
        """
        Adds an event to the event queue
        """
        await self.event_queue.put(event)

    async def _send_event(self, event: BarcodeEvent):
        """
        Sends the given event to the notification target
        :param event: barcode event
        """
        raise NotImplementedError()
