from prometheus_client import Gauge, Summary

from barcode_server.const import *

WEBSOCKET_CLIENT_COUNT = Gauge(
    'websocket_client_count',
    'Number of currently connected websocket clients'
)

DEVICES_COUNT = Gauge(
    'devices_count',
    'Number of currently detected devices'
)

SCAN_COUNT = Gauge(
    'scan_count',
    'Number of times a scan has been detected'
)

DEVICE_DETECTION_TIME = Summary('device_detection_processing_seconds', 'Time spent detecting devices')

REST_TIME = Summary('rest_endpoint_processing_seconds', 'Time spent in a rest command handler', ['endpoint'])
REST_TIME_DEVICES = REST_TIME.labels(endpoint=ENDPOINT_DEVICES)

NOTIFIER_TIME = Summary('notifier_processing_seconds', 'Time spent in a notifier', ['type'])
WEBSOCKET_NOTIFIER_TIME = NOTIFIER_TIME.labels(type='websocket')
HTTP_NOTIFIER_TIME = NOTIFIER_TIME.labels(type='http')
MQTT_NOTIFIER_TIME = NOTIFIER_TIME.labels(type='mqtt')
