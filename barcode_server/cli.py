import asyncio
import logging
import os
import signal
import sys

import click
from container_app_conf.formatter.toml import TomlFormatter
from prometheus_client import start_http_server

parent_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), "..", ".."))
sys.path.append(parent_dir)

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


def signal_handler(signal=None, frame=None):
    LOGGER.info("Exiting...")
    os._exit(0)


CMD_OPTION_NAMES = {
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
    LOGGER = logging.getLogger("barcode_server")
    LOGGER.setLevel(log_level)

    LOGGER.info("=== barcode-server ===")
    LOGGER.info(f"Instance ID: {config.INSTANCE_ID.value}")

    barcode_reader = BarcodeReader(config)
    webserver = Webserver(config, barcode_reader)

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
