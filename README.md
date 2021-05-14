# barcode-server [![Code Climate](https://codeclimate.com/github/markusressel/barcode-server.svg)](https://codeclimate.com/github/markusressel/barcode-server)

A simple daemon to read barcodes from USB Barcode Scanners
and expose them to other service using a websocket API.

[![asciicast](https://asciinema.org/a/366004.svg)](https://asciinema.org/a/366004)

# Features

* [x] Autodetect Barcode Scanner devices on the fly
* [x] Request Server information via [REST API](#rest-api)
* [x] Subscribe to barcode events using
    * [x] [Websocket API](#websocket-api)
* [x] Push barcode events using
    * [x] [HTTP requests](#http-request)
    * [x] [MQTT messages](#mqtt-publish)
* [x] Get [statistics](#statistics) via Prometheus exporter


# How to use

## Device Access Permissions

Ensure the user running this application is in the correct group for accessing
input devices (usually `input`), like this:
```
sudo usermod -a -G input myusername
```
## Native

```
# create venv
python -m venv ./venv
# enter venv
source ./venv/bin/activate
# install barcode-server
pip install barcode-server
# exit venv
deactivate

# print config
./venv/bin/barcode-server config

# launch application
./venv/bin/barcode-server run
```

## Docker

When starting the docker container, make sure to pass through input devices:
```
docker run \
  --name barcode \
  --device=/dev/input \
  -e PUID=0 \
  -e PGID=0 \
  markusressel/barcode-server
```
**Note:** Although **barcode-server** will continuously try to detect new devices,
even when passing through `/dev/input` like shown above, new devices can not be detected
due to the way docker works. If you need to detect devices in real-time, you have to use
the native approach.

You can specify the user id and group id using the `PUID` and `PGID` environment variables.

# Webserver

By default the webserver will listen to `127.0.0.1` on port `9654`.

## Authorization

When specified in the config, an API token is required to authorize clients, which must
be passed using a `X-Auth-Token` header when connecting. Since barcode-scanner doesn't rely on any
persistence, the token is specified in the configuration file and can not be changed on runtime.

## Rest API

**barcode-server** provides a simple REST API to get some basic information.
This API can **not** be used to retrieve barcode events. To do that you have to use one of
the approaches described below.

| Endpoint   | Description                               |
|------------|-------------------------------------------|
| `/devices` | A list of all currently detected devices. |

## Websocket API

In addition to the REST API **barcode-server** also exposes a websocket at `/`, which can be used
to get realtime barcode scan events.

To connect to it, you have to provide

* a `Client-ID` header with a UUID (v4)
* (optional) an empty `Drop-Event-Queue` header, to ignore events that happened between connections
* (optional) an `X-Auth-Token` header, to authorize the client

Messages received on this websocket are JSON formatted strings with the following format:
```json
{
  "date": "2020-08-03T10:00:00+00:00",
  "device": {
    "name": "BARCODE SCANNER BARCODE SCANNER",
    "path": "/dev/input/event3",
    "vendorId": "ffff",
    "productId": "0035",
  },
  "barcode": "4250168519463"
}
```

To test the connection you can use f.ex. `websocat`:

```
> websocat - autoreconnect:ws://127.0.0.1:9654 --text --header "Client-ID:dc1f14fc-a7a6-4102-af60-2b6e0dcf744c" --header "Drop-Event-Queue:" --header "X-Auth-Token:EmUSqjXGfnQwn5wn6CpzJRZgoazMTRbMNgH7CXwkQG7Ph7stex"
{"date":"2020-12-20T19:35:04.769739","device":{"name":"BARCODE SCANNER BARCODE SCANNER","path":"/dev/input/event3","vendorId":65535,"productId":53},"barcode":"D-t38409355843o52230Lm54784"}
{"date":"2020-12-20T19:35:06.237408","device":{"name":"BARCODE SCANNER BARCODE SCANNER","path":"/dev/input/event3","vendorId":65535,"productId":53},"barcode":"4250168519463"}
```

## HTTP Request

When configured, you can let **barcode-scanner** issue a HTTP request (defaults to `POST`) when a
barcode is scanned, which provides the ability to push barcode events to a server that is unaware
of any client. The body of the request will contain the same JSON as in the websocket API example.

To do this simply add the following section to your config:
```yaml
barcode_server:
  [...]
  http:
    url: "https://my.domain.com/barcode"
```

Have a look at the [example config](barcode_server.yaml) for more options.

## MQTT Publish

When configured, you can let **barcode-scanner** publish barcode events to a MQTT broker.
The payload of the message will contain the same JSON as in the websocket API example.

To do this simply add the following section to your config:
```yaml
barcode_server:
  [...]
  mqtt:
    host: "my.mqtt.broker"
```

Have a look at the [example config](barcode_server.yaml) for more options.

## Statistics

**barcode-server** exposes a prometheus exporter (defaults to port `8000`) to give some statistical insight.

# FAQ

## Can I lock the Barcode Scanner to this application?

Yes. Most barcode readers normally work like a keyboard, resulting in their input being evaluated by
the system, which can clutter up your TTY or other open programs.
**barcode-server** will try to _grab_ input devices, making it the sole recipient of all
incoming input events from those devices, which should prevent the device from cluttering
your TTY.

If, for some reason, this does not work for you, try this:

Create a file `/etc/udev/rules.d/10-barcode.rules`:
```
SUBSYSTEM=="input", ACTION=="add", ATTRS{idVendor}=="xxxx", ATTRS{idProduct}=="yyyy", RUN+="/bin/sh -c 'echo remove > /sys$env{DEVPATH}/uevent'"
SUBSYSTEM=="input", ACTION=="add", ATTRS{idVendor}=="xxxx", ATTRS{idProduct}=="yyyy", DEVPATH=="*:1.0/*", KERNEL=="event*", RUN+="/bin/sh -c 'ln -sf /dev/input/$kernel /dev/input/barcode_scanner'"
```
Replace the `idVendor` and `idProduct` values with the values of your barcode reader (a 4 digit hex value with leading zeros).
You can find them in the log output of **barcode-reader** or using `lsusb` with the wireless receiver attached to your computer.

Reload udev rules using:
```
udevadm control --reload
```
then remove and reinsert the wireless receiver.
You should now have a symlink in `/dev/input/barcode_scanner`:
```
ls -lha /dev/input/barcode_scanner
```
which can be used in the `device_paths` section of the **barcode-server** config.

Source: [This](https://serverfault.com/questions/385260/bind-usb-keyboard-exclusively-to-specific-application/976557#976557)
and [That](https://stackoverflow.com/questions/63478999/how-to-make-linux-ignore-a-keyboard-while-keeping-it-available-for-my-program-to/63531743#63531743)

# Contributing

GitHub is for social coding: if you want to write code, I encourage contributions
through pull requests from forks of this repository. Create GitHub tickets for
bugs and new features and comment on the ones that you are interested in.

# License

```text
barcode-server is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```
