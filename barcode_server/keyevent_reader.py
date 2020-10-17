import logging

from evdev import KeyEvent, InputDevice, categorize

LOGGER = logging.getLogger(__name__)


class KeyEventReader:
    """
    Class used to convert a sequence of KeyEvents to text
    """

    def __init__(self):
        self._shift = False
        self._caps = False
        self._alt = False

        self._line = ""

    def read_line(self, input_device: InputDevice) -> str:
        """
        Reads a line
        :param input_device: the device to read from
        :return: line
        """
        self._line = ""
        # While there is a function called async_read_loop, it tends
        # to skip input events, so we use the non-async read-loop here.

        # async for event in input_device.async_read_loop():
        for event in input_device.read_loop():
            event = categorize(event)
            if isinstance(event, KeyEvent):
                if self._on_key_event(event):
                    return self._line

    def _on_key_event(self, event: KeyEvent) -> bool:
        LOGGER.debug(str(event))
        # if event.type == evdev.ecodes.EV_KEY and event.value == 1:
        if event.keycode == "KEY_ENTER" or event.keycode == "KEY_KPENTER":
            if event.keystate == event.key_up:
                # line is finished
                return True
        elif event.keycode == "KEY_RIGHTSHIFT" or event.keycode == "KEY_LEFTSHIFT":
            if event.keystate in [event.key_down, event.key_hold]:
                self._shift = True
            else:
                self._shift = False
        elif event.keycode == "KEY_LEFTALT" or event.keycode == "KEY_RIGHTALT":
            if event.keystate in [event.key_down, event.key_hold]:
                self._alt = True
            else:
                self._alt = False
        elif event.keycode == "KEY_BACKSPACE":
            self._line = self._line[:-1]
        elif event.keystate == event.key_down:
            character = None

            if len(event.keycode) == 5:
                character = event.keycode[-1]
            elif event.keycode == "KEY_MINUS":
                character = '-'
            elif event.keycode == "KEY_SPACE":
                character = ' '
            elif event.keycode.startswith("KEY_KP"):
                if len(event.keycode) == 7:
                    character = event.keycode[-1]
                elif event.keycode == "KEY_KPASTERISK":
                    character = '*'
                elif event.keycode == "KEY_KPCOMMA":
                    character = ','
                elif event.keycode == "KEY_KPDOT":
                    character = '.'
                elif event.keycode == "KEY_KPEQUAL":
                    character = '='
                elif event.keycode == "KEY_KPJPCOMMA":
                    character = ','
                elif event.keycode == "KEY_KPLEFTPAREN":
                    character = '('
                elif event.keycode == "KEY_KPMINUS":
                    character = '-'
                elif event.keycode == "KEY_KPPLUS":
                    character = '+'
                elif event.keycode == "KEY_KPPLUSMINUS":
                    character = '+-'
                elif event.keycode == "KEY_KPRIGHTPAREN":
                    character = ')'
                elif event.keycode == "KEY_KPSLASH":
                    character = '/'

            if character is None:
                character = event.keycode[4:]
                if len(character) > 1:
                    LOGGER.warning(f"Unhandled Keycode: {event.keycode}")

            if self._shift or self._caps:
                character = character.upper()
            else:
                character = character.lower()

            # append the current character
            self._line += character

        return False
