from evdev import InputDevice


def input_device_to_dict(input_device: InputDevice) -> dict:
    return {
        "name": input_device.name,
        "path": input_device.path,
        "vendorId": f"{input_device.info.vendor: 04x}",
        "productId": f"{input_device.info.product: 04x}",
    }


def barcode_event_to_json(input_device: InputDevice, barcode: str) -> bytes:
    import orjson

    event = {
        "device": input_device_to_dict(input_device),
        "barcode": barcode
    }

    json = orjson.dumps(event)
    return json
