from typing import List
from unittest.mock import Mock

from evdev import InputEvent, ecodes, KeyEvent

from barcode_server.keyevent_reader import KeyEventReader
from tests import TestBase


class KeyEventReaderTest(TestBase):

    @staticmethod
    def fake_input_loop(input: List[InputEvent]):
        input_events = input

        def read_loop():
            for event in input_events:
                yield event

        return read_loop

    @staticmethod
    def mock_input_event(keycode, keystate) -> InputEvent:
        input_event = Mock()
        input_event.type = 1
        input_event.keystate = keystate  # 0: UP, 1: Down, 2: Hold
        input_event.keycode = keycode
        # inverse lookup of the event code in the target structure
        code = next(key for key, value in ecodes.keys.items() if value == keycode)
        input_event.code = code

        return input_event

    def generate_input_event_sequence(self, expected: str, finish_line: bool = True) -> List[InputEvent]:
        events = []
        keycodes = list(map(lambda x: self.character_to_keycode(x), expected))

        for item in keycodes:
            for keystate in [KeyEvent.key_down, KeyEvent.key_up]:
                event = self.mock_input_event(keycode=item, keystate=keystate)
                events.append(event)

        if finish_line:
            for keystate in [KeyEvent.key_down, KeyEvent.key_up]:
                event = self.mock_input_event(keycode="KEY_ENTER", keystate=keystate)
                events.append(event)

        return events

    @staticmethod
    def character_to_keycode(character: str) -> str:
        char_to_keycode_map = {
            '0': "KEY_KP0",
            '1': "KEY_KP1",
            '2': "KEY_KP2",
            '3': "KEY_KP3",
            '4': "KEY_KP4",
            '5': "KEY_KP5",
            '6': "KEY_KP6",
            '7': "KEY_KP7",
            '8': "KEY_KP8",
            '9': "KEY_KP9",

            '*': "KEY_KPASTERISK",
            '/': "KEY_SLASH",
            '-': "KEY_KPMINUS",
            '+': "KEY_KPPLUS",
            '.': "KEY_DOT",
            ',': "KEY_COMMA",
            '?': "KEY_QUESTION",

            '\n': "KEY_ENTER",
        }
        return char_to_keycode_map[character]

    def test_mock_gen(self):
        # GIVEN
        expected = [
            self.mock_input_event(keycode="KEY_KPMINUS", keystate=KeyEvent.key_down),
            self.mock_input_event(keycode="KEY_KPMINUS", keystate=KeyEvent.key_up),

            self.mock_input_event(keycode="KEY_DOT", keystate=KeyEvent.key_down),
            self.mock_input_event(keycode="KEY_DOT", keystate=KeyEvent.key_up),

            self.mock_input_event(keycode="KEY_KPMINUS", keystate=KeyEvent.key_down),
            self.mock_input_event(keycode="KEY_KPMINUS", keystate=KeyEvent.key_up),

            self.mock_input_event(keycode="KEY_ENTER", keystate=KeyEvent.key_down),
            self.mock_input_event(keycode="KEY_ENTER", keystate=KeyEvent.key_up),
        ]
        text = "-.-"

        # WHEN
        input_events = self.generate_input_event_sequence(text)

        # THEN
        self.assertEqual(len(expected), len(input_events))
        for i in range(0, len(expected)):
            self.assertEqual(expected[i].keycode, input_events[i].keycode)

    async def test_numbers(self):
        # GIVEN
        under_test = KeyEventReader()
        expected = "0123456789"
        input_events = self.generate_input_event_sequence(expected)
        input_device = Mock()
        input_device.read_loop = self.fake_input_loop(input_events)

        # WHEN
        line = under_test.read_line(input_device)

        # THEN
        self.assertEqual(expected, line)

    async def test_special_characters(self):
        # GIVEN
        under_test = KeyEventReader()
        expected = ".,*/+-?"
        input_events = self.generate_input_event_sequence(expected)
        input_device = Mock()
        input_device.read_loop = self.fake_input_loop(input_events)

        # WHEN
        line = under_test.read_line(input_device)

        # THEN
        self.assertEqual(expected, line)
