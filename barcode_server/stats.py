from prometheus_client import Gauge

DEVICES_COUNT = Gauge(
    'devices_count',
    'Number of devices currently detected'
)

SCAN_COUNT = Gauge(
    'scan_count',
    'Number of times a scan has been detected'
)
