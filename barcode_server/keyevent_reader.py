import logging

from evdev import KeyEvent, InputDevice, categorize

LOGGER = logging.getLogger(__name__)

US_EN_UPPER_DICT = {
    "`": "~",
    "1": "!",
    "2": "@",
    "3": "#",
    "4": "$",
    "5": "%",
    "6": "^",
    "7": "&",
    "8": "*",
    "9": "(",
    "0": ")",
    "-": "_",
    "=": "+",
    ",": "<",
    ".": ">",
    "/": "?",
    ";": ":",
    "'": "\"",
    "\\": "|",
    "[": "{",
    "]": "}"
}


class KeyEventReader:
    """
    Class used to convert a sequence of KeyEvents to text
    """

    def __init__(self):
        self._shift = False
        self._caps = False
        self._alt = False
        self._unicode_number_input_buffer = ""

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
            try:
                event = categorize(event)

                if hasattr(event, "event"):
                    if not hasattr(event, "keystate") and hasattr(event.event, "keystate"):
                        event.keystate = event.event.keystate

                if not hasattr(event, "keystate") or not hasattr(event, "keycode"):
                    continue

                keycode = event.keycode
                keystate = event.keystate

                if isinstance(event, KeyEvent):
                    if self._on_key_event(keycode, keystate):
                        return self._line
                elif hasattr(event, "event") and event.event.type == 1:
                    if self._on_key_event(keycode, keystate):
                        return self._line
            except Exception as ex:
                LOGGER.exception(ex)

    def _on_key_event(self, code: str, state: int) -> bool:
        if code in ["KEY_ENTER", "KEY_KPENTER"]:
            if state == KeyEvent.key_up:
                # line is finished
                self._reset_modifiers()
                return True
        elif code in ["KEY_RIGHTSHIFT", "KEY_LEFTSHIFT"]:
            if state in [KeyEvent.key_down, KeyEvent.key_hold]:
                self._shift = True
            else:
                self._shift = False
        elif code in ["KEY_LEFTALT", "KEY_RIGHTALT"]:
            if state in [KeyEvent.key_down, KeyEvent.key_hold]:
                self._alt = True
            else:
                self._alt = False

                character = self._unicode_numbers_to_character(self._unicode_number_input_buffer)
                self._unicode_number_input_buffer = ""

                if character is not None:
                    self._line += character

        elif code == "KEY_BACKSPACE":
            self._line = self._line[:-1]
        elif state == KeyEvent.key_down:
            character = self._code_to_character(code)
            if self._alt:
                self._unicode_number_input_buffer += character
            else:
                if character is not None and not self._alt:
                    # append the current character
                    self._line += character

        return False

    def _code_to_character(self, code: str) -> chr or None:
        character = None

        if len(code) == 5:
            character = code[-1]
        elif code.startswith("KEY_KP") and len(code) == 7:
            character = code[-1]

        elif code in ["KEY_DOWN"]:
            character = '\n'
        elif code in ["KEY_SPACE"]:
            character = ' '
        elif code in ["KEY_ASTERISK", "KEY_KPASTERISK"]:
            character = '*'
        elif code in ["KEY_MINUS", "KEY_KPMINUS"]:
            character = '-'
        elif code in ["KEY_PLUS", "KEY_KPPLUS"]:
            character = '+'
        elif code in ["KEY_QUESTION"]:
            character = '?'
        elif code in ["KEY_COMMA", "KEY_KPCOMMA"]:
            character = ','
        elif code in ["KEY_DOT", "KEY_KPDOT"]:
            character = '.'
        elif code in ["KEY_EQUAL", "KEY_KPEQUAL"]:
            character = '='
        elif code in ["KEY_LEFTPAREN", "KEY_KPLEFTPAREN"]:
            character = '('
        elif code in ["KEY_PLUSMINUS", "KEY_KPPLUSMINUS"]:
            character = '+-'
        elif code in ["KEY_RIGHTPAREN", "KEY_KPRIGHTPAREN"]:
            character = ')'
        elif code in ["KEY_RIGHTBRACE"]:
            character = ']'
        elif code in ["KEY_LEFTBRACE"]:
            character = '['
        elif code in ["KEY_SLASH", "KEY_KPSLASH"]:
            character = '/'
        elif code in ["KEY_BACKSLASH"]:
            character = '\\'
        elif code in ["KEY_COLON"]:
            character = ';'
        elif code in ["KEY_SEMICOLON"]:
            character = ';'
        elif code in ["KEY_APOSTROPHE"]:
            character = '\''
        elif code in ["KEY_GRAVE"]:
            character = '`'

        if character is None:
            character = code[4:]
            if len(character) > 1:
                LOGGER.warning(f"Unhandled Keycode: {code}")

        if self._shift or self._caps:
            character = character.upper()
            if character in US_EN_UPPER_DICT.keys():
                character = US_EN_UPPER_DICT[character]
        else:
            character = character.lower()

        return character

    @staticmethod
    def _unicode_numbers_to_character(code: str) -> chr or None:
        if code is None or len(code) <= 0:
            return None

        try:
            # convert to hex
            i = int(code)
            h = hex(i)
            s = f"{h}"

            return bytearray.fromhex(s[2:]).decode('utf-8')
        except Exception as ex:
            LOGGER.exception(ex)
            return None

    def _reset_modifiers(self):
        self._alt = False
        self._unicode_number_input_buffer = ""
        self._shift = False
        self._caps = False
