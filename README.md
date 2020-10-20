# barcode-server

A simple daemon to read barcodes from USB Barcode Scanners
and expose them to other service using a websocket API.

[![asciicast](https://asciinema.org/a/366004.svg)](https://asciinema.org/a/366004)

# How to use

## Device Access Permissions

Ensure the user running this application is in the correct group for accessing
input devices (usually `input`), like this:
```
sudo usermod -a -G input myusername
```

## Docker

When starting the docker container, make sure to pass through input devices:
```
docker run
  --name barcode \
  --device=/dev/input \
  markusressel/barcode-server
```

# API

By default the service will expose a websocket on `127.0.0.1` on port `9654`.
When specified in the config, an API token is required to authorize clients, which must be passed using a `X-Auth-Token` header when connecting.
Since barcode-scanner is stateless, the token is specified in the configuration file.

Messages received on this websocket are JSON formatted strings with the following format:
```json
{
  "device": {
    "name": "BARCODE SCANNER BARCODE SCANNER",
    "path": "/dev/input/event3",
    "vendorId": "ffff",
    "productId": "0035",
  },
  "barcode": "4250168519463"
}
```

To test things out you can use f.ex. `websocat`:

```
> websocat ws://127.0.0.1:9654 --header "X-Auth-Token:EmUSqjXGfnQwn5wn6CpzJRZgoazMTRbMNgH7CXwkQG7Ph7stex"
{"device":{"name":"BARCODE SCANNER BARCODE SCANNER","path":"/dev/input/event3","vendorId":65535,"productId":53},"barcode":"D-t38409355843o52230Lm54784"}
{"device":{"name":"BARCODE SCANNER BARCODE SCANNER","path":"/dev/input/event3","vendorId":65535,"productId":53},"barcode":"4250168519463"}
```

# FAQ

## Can I lock the Barcode Scanner to this application?

Most barcode readers normally work like a keyboard, resulting in their input being evaluated by
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
