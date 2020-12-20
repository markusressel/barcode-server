from evdev import InputDevice

from barcode_server.barcode import BarcodeEvent


def input_device_to_dict(input_device: InputDevice) -> dict:
    return {
        "name": input_device.name,
        "path": input_device.path,
        "vendorId": f"{input_device.info.vendor: 04x}",
        "productId": f"{input_device.info.product: 04x}",
    }


def barcode_event_to_json(event: BarcodeEvent) -> bytes:
    import orjson

    event = {
        "date": event.date.isoformat(),
        "device": input_device_to_dict(event.input_device),
        "barcode": event.barcode
    }

    json = orjson.dumps(event)
    return json
