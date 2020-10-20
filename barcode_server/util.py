from evdev import InputDevice


def barcode_event_to_json(input_device: InputDevice, barcode: str) -> bytes:
    import orjson

    event = {
        "device": {
            "name": input_device.name,
            "path": input_device.path,
            "vendorId": f"{input_device.info.vendor: 04x}",
            "productId": f"{input_device.info.product: 04x}",
        },
        "barcode": barcode
    }

    json = orjson.dumps(event)
    return json
