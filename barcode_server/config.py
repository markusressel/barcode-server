#  Copyright (c) 2019 Markus Ressel
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
import logging
import re

from container_app_conf import ConfigBase
from container_app_conf.entry.bool import BoolConfigEntry
from container_app_conf.entry.file import FileConfigEntry
from container_app_conf.entry.int import IntConfigEntry
from container_app_conf.entry.list import ListConfigEntry
from container_app_conf.entry.regex import RegexConfigEntry
from container_app_conf.entry.string import StringConfigEntry
from container_app_conf.entry.timedelta import TimeDeltaConfigEntry
from container_app_conf.source.env_source import EnvSource
from container_app_conf.source.toml_source import TomlSource
from container_app_conf.source.yaml_source import YamlSource
from py_range_parse import Range

from barcode_server.const import *


class AppConfig(ConfigBase):

    def __new__(cls, *args, **kwargs):
        yaml_source = YamlSource(CONFIG_NODE_ROOT)
        toml_source = TomlSource(CONFIG_NODE_ROOT)
        data_sources = [
            EnvSource(),
            yaml_source,
            toml_source,
        ]
        return super(AppConfig, cls).__new__(cls, data_sources=data_sources)

    LOG_LEVEL = StringConfigEntry(
        description="Log level",
        key_path=[
            CONFIG_NODE_ROOT,
            "log_level"
        ],
        regex=re.compile(f" {'|'.join(logging._nameToLevel.keys())}", flags=re.IGNORECASE),
        default="INFO",
    )

    SERVER_HOST = StringConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_SERVER,
            "host"
        ],
        default=DEFAULT_SERVER_HOST,
        secret=True)

    SERVER_PORT = IntConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_SERVER,
            CONFIG_NODE_PORT
        ],
        range=Range(1, 65534),
        default=9465)

    SERVER_API_TOKEN = StringConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_SERVER,
            "api_token"
        ],
        required=True,
        secret=True
    )

    DROP_EVENT_QUEUE_AFTER = TimeDeltaConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            "drop_event_queue_after"
        ],
        default="2h",
    )

    RETRY_INTERVAL = TimeDeltaConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            "retry_interval"
        ],
        default="2s",
    )

    HTTP_METHOD = StringConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_HTTP,
            "method"
        ],
        required=True,
        default="POST",
        regex="GET|POST|PUT|PATCH"
    )

    HTTP_URL = StringConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_HTTP,
            "url"
        ],
        required=False
    )

    HTTP_HEADERS = ListConfigEntry(
        item_type=StringConfigEntry,
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_HTTP,
            "headers"
        ],
        default=[]
    )

    MQTT_HOST = StringConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_MQTT,
            "host"
        ],
        required=False
    )
    MQTT_PORT = IntConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_MQTT,
            "port"
        ],
        required=True,
        default=1883,
        range=Range(1, 65534),
    )

    MQTT_CLIENT_ID = StringConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_MQTT,
            "client_id"
        ],
        default="barcode-server"
    )

    MQTT_USER = StringConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_MQTT,
            "user"
        ]
    )

    MQTT_PASSWORD = StringConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_MQTT,
            "password"
        ],
        secret=True
    )

    MQTT_TOPIC = StringConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_MQTT,
            "topic"
        ],
        default="barcode-server/barcode",
        required=True
    )

    MQTT_QOS = IntConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_MQTT,
            "qos"
        ],
        default=2,
        required=True
    )

    MQTT_RETAIN = BoolConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_MQTT,
            "retain"
        ],
        default=False,
        required=True
    )

    DEVICE_PATTERNS = ListConfigEntry(
        item_type=RegexConfigEntry,
        item_args={
            "flags": re.IGNORECASE
        },
        key_path=[
            CONFIG_NODE_ROOT,
            "devices"
        ],
        default=[]
    )

    DEVICE_PATHS = ListConfigEntry(
        item_type=FileConfigEntry,
        key_path=[
            CONFIG_NODE_ROOT,
            "device_paths"
        ],
        default=[]
    )

    STATS_PORT = IntConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_STATS,
            CONFIG_NODE_PORT
        ],
        default=8000,
        required=False
    )

    def validate(self):
        super(AppConfig, self).validate()
        if len(self.DEVICE_PATHS.value) == len(self.DEVICE_PATTERNS.value) == 0:
            raise AssertionError("You must provide at least one device pattern or device_path!")
