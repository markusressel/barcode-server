import asyncio
import logging
import os
import signal
import sys

import click
from container_app_conf.formatter.toml import TomlFormatter
from prometheus_async.aio.web import start_http_server

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

loop = asyncio.get_event_loop()


def signal_handler(signal=None, frame=None):
    LOGGER.info("Exiting...")
    os._exit(0)


CMD_OPTION_NAMES = {
    # PARAM_SKIP_ANALYSE_PHASE: ['--skip-analyse-phase', '-sap'],
    # PARAM_DRY_RUN: ['--dry-run', '-dr']
}

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def cli():
    pass


def get_option_names(parameter: str) -> list:
    """
    Returns a list of all valid console parameter names for a given parameter
    :param parameter: the parameter to check
    :return: a list of all valid names to use this parameter
    """
    return CMD_OPTION_NAMES[parameter]


@cli.command(name="run")
# @click.option(*get_option_names(PARAM_DRY_RUN), required=False, default=None, is_flag=True,
#               help='When set no files or folders will actually be deleted but a preview of '
#                    'what WOULD be done will be printed.')
def c_run():
    """
    Run the barcode-server
    """
    from barcode_server.barcode import BarcodeReader
    from barcode_server.config import AppConfig
    from barcode_server.webserver import Webserver

    signal.signal(signal.SIGINT, signal_handler)

    config = AppConfig()

    log_level = logging._nameToLevel.get(str(config.LOG_LEVEL.value).upper(), config.LOG_LEVEL.default)
    logging.getLogger("barcode_server").setLevel(log_level)

    barcode_reader = BarcodeReader(config)
    webserver = Webserver(config, barcode_reader)

    logging.debug("Starting...")

    # start prometheus server
    if config.STATS_PORT.value is not None:
        LOGGER.info("Starting statistics webserver...")
        start_http_server(config.STATS_PORT.value)

    tasks = asyncio.gather(
        webserver.start(),
    )

    loop.run_until_complete(tasks)
    loop.run_forever()


@cli.command(name="config")
def c_config():
    """
    Print the current configuration of barcode-server
    """
    from barcode_server.config import AppConfig

    config = AppConfig()
    click.echo(config.print(TomlFormatter()))


if __name__ == '__main__':
    cli()
