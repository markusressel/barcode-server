# barcode-forwarder

A simple daemon to read barcodes from a USB Barcode Scanner and forward them to some other service.

# How to use

Ensure the user running this application is in the correct group for accessing
input devices (usually `input`), like this:
```
sudo usermod -a -G input myusername
```

## Docker

When starting the docker container, make sure to pass though input devices:
```
docker run
  --name barcode \
  --device=/dev/input
  markusressel/barcode-forwarder
```

## Block keyboard input

Normally the barcode reader works like any keyboard, meaning its input is
evaluated by the system, which can clutter up your TTY or other open
programs. To prevent this:

Create a file `/etc/udev/rules.d/10-barcode.rules`:
```
SUBSYSTEM=="input", ACTION=="add", ATTRS{idVendor}=="xxxx", ATTRS{idProduct}=="yyy", RUN+="/bin/sh -c 'echo remove > /sys$env{DEVPATH}/uevent'"
ACTION=="add", ATTRS{idVendor}=="xxxx", ATTRS{idProduct}=="yyyy", SYMLINK+="barcode"
```
Replace the `idVendor` and `idProduct` values with the values of your barcode reader.
You can find them in the log output of **barcode-reader**.

Source: [This](https://serverfault.com/questions/385260/bind-usb-keyboard-exclusively-to-specific-application/976557#976557)
and [That](https://stackoverflow.com/questions/63478999/how-to-make-linux-ignore-a-keyboard-while-keeping-it-available-for-my-program-to/63531743#63531743)

# Contributing

GitHub is for social coding: if you want to write code, I encourage contributions
through pull requests from forks of this repository. Create GitHub tickets for
bugs and new features and comment on the ones that you are interested in.

# License

```text
barcode-forwarder is free software: you can redistribute it and/or modify
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