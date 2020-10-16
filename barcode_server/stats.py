from prometheus_client import Gauge

SCAN_COUNT = Gauge(
    'scan_count',
    'Number of times a scan has been detected'
)
