import asyncio
import logging
import os
import sys

from barcode_forwarder.barcode import BarcodeReader
from barcode_forwarder.config import AppConfig
from barcode_forwarder.webserver import Webserver

"""
Simple script to read barcodes from a USB connected barcode reader.

Ensure the user running this script is in the correct group for accessing
input devices (usually `input`), like this:
> sudo usermod -a -G input myusername

Normally the barcode reader works like any keyboard, meaning its input is
evaluated by the system, which can clutter up your TTY or other open
programs. To prevent this:

Create a file `/etc/udev/rules.d/10-barcode.rules`:
```
SUBSYSTEM=="input", ACTION=="add", ATTRS{idVendor}=="xxxx", ATTRS{idProduct}=="yyy", RUN+="/bin/sh -c 'echo remove > /sys$env{DEVPATH}/uevent'"
ACTION=="add", ATTRS{idVendor}=="xxxx", ATTRS{idProduct}=="yyyy", SYMLINK+="barcode"
```
Replace the idVendor and idProduct with the values of your barcode reader.

https://serverfault.com/questions/385260/bind-usb-keyboard-exclusively-to-specific-application/976557#976557
https://stackoverflow.com/questions/63478999/how-to-make-linux-ignore-a-keyboard-while-keeping-it-available-for-my-program-to/63531743#63531743
"""

parent_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), "..", ".."))
sys.path.append(parent_dir)

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

if __name__ == '__main__':
    config = AppConfig()

    log_level = logging._nameToLevel.get(str(config.LOG_LEVEL.value).upper(), config.LOG_LEVEL.default)
    logging.getLogger("barcode_forwarder").setLevel(log_level)

    barcode_reader = BarcodeReader(config)
    webserver = Webserver(config)

    logging.debug("Starting...")

    tasks = asyncio.gather(
        barcode_reader.start(),
        webserver.start()
    )

    asyncio.get_event_loop().run_until_complete(tasks)

    logging.debug("Exiting...")
