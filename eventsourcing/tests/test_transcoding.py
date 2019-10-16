import datetime
from collections import deque, namedtuple

import sys

if sys.version_info >= (3, 7):
    from dataclasses import dataclass

from decimal import Decimal
from unittest import TestCase
from uuid import NAMESPACE_URL

from eventsourcing.utils.times import utc_timezone
from eventsourcing.utils.transcoding import (
    ObjectJSONDecoder,
    ObjectJSONEncoder,
    json_loads,
)


class TestObjectJSONEncoder(TestCase):
    def test_encode(self):
        encoder = ObjectJSONEncoder()

        value = 1
        expect = "1"
        self.assertEqual(encoder.encode(value), expect)

        value = datetime.datetime(2011, 1, 1, 1, 1, 1)
        expect = '{"ISO8601_datetime": "2011-01-01T01:01:01.000000"}'
        self.assertEqual(encoder.encode(value), expect)

        value = datetime.datetime(2011, 1, 1, 1, 1, 1, tzinfo=utc_timezone)
        expect = '{"ISO8601_datetime": "2011-01-01T01:01:01.000000+0000"}'
        self.assertEqual(encoder.encode(value), expect)

        value = datetime.date(2011, 1, 1)
        expect = '{"ISO8601_date": "2011-01-01"}'
        self.assertEqual(expect, encoder.encode(value))

        value = datetime.time(23, 59, 59, 123456)
        expect = '{"ISO8601_time": "23:59:59.123456"}'
        self.assertEqual(encoder.encode(value), expect)

        value = Decimal("59.123456")
        expect = '{"__decimal__": "59.123456"}'
        self.assertEqual(encoder.encode(value), expect)

        value = NAMESPACE_URL
        expect = '{"UUID": "6ba7b8119dad11d180b400c04fd430c8"}'
        self.assertEqual(encoder.encode(value), expect)

        value = MyObjectClass(NAMESPACE_URL)
        self.assertEqual(
            value.__class__.__module__,
            "eventsourcing.tests.test_transcoding",
            "Module does not have full path, Python 2.7 issue with unittest"
            " (need to run test from root dir",
        )
        expect = (
            '{"__class__": {"state": {"a": {"UUID": "6ba7b8119dad11d18'
            '0b400c04fd430c8"}}, "topic": "eventsourcing.tests.test_tr'
            'anscoding#MyObjectClass"}}'
        )
        self.assertEqual(encoder.encode(value), expect)

        value = tuple([1, 2, 4])
        encoded = encoder.encode(value)
        expected = '{"__tuple__": {"state": [1, 2, 4], "topic": "builtins#tuple"}}'
        self.assertEqual(encoded, expected)

        value = MyNamedTuple(a=1, b="2", c=MyObjectClass([3, "4"]))
        expected = (
            '{"__tuple__": {"state": [1, "2", {"__class__": {"state": '
            '{"a": [3, "4"]}, "topic": "eventsourcing.tests.test_trans'
            'coding#MyObjectClass"}}], "topic": "eventsourcing.tests.t'
            'est_transcoding#MyNamedTuple"}}'
        )
        self.assertEqual(encoder.encode(value), expected)

        if sys.version_info >= (3, 7):
            value = MyDataClass(1, "2", Decimal("3.0"))
            expected = (
                '{"__class__": {"state": {"a": 1, "b": "2", "c": {'
                '"__decimal__": "3.0"}}, "topic": "eventsourcing.t'
                'ests.test_transcoding#MyDataClass"}}'
            )
            self.assertEqual(encoder.encode(value), expected)

        value = deque()
        expect = '{"__deque__": []}'
        self.assertEqual(encoder.encode(value), expect)

        # Check defers to base class to raise TypeError.
        # - a type isn't supported at the moment, hence this test works
        with self.assertRaises(TypeError):
            encoder.encode(object)

    def check_encoded_value(self, encoder, value, expect):
        actual = encoder.encode(value)
        try:
            self.assertEqual(
                expect, actual, (type(expect), type(actual), expect, actual)
            )
        except:
            print()
            print(actual)
            print(expect)


class TestObjectJSONDecoder(TestCase):
    def test_decode(self):
        decoder = ObjectJSONDecoder()
        self.assertEqual(decoder.decode("1"), 1)

        value = '{"ISO8601_datetime": "2011-01-01T01:01:01.000000"}'
        expect = datetime.datetime(2011, 1, 1, 1, 1, 1)
        self.assertEqual(decoder.decode(value), expect)

        value = '{"ISO8601_datetime": "2011-01-01T01:01:01.000000+0000"}'
        expect = datetime.datetime(2011, 1, 1, 1, 1, 1, tzinfo=utc_timezone)
        self.assertEqual(decoder.decode(value), expect)

        value = '{"ISO8601_date": "2011-01-01"}'
        expect = datetime.date(2011, 1, 1)
        self.assertEqual(decoder.decode(value), expect)

        value = '{"UUID": "6ba7b8119dad11d180b400c04fd430c8"}'
        expect = NAMESPACE_URL
        self.assertEqual(decoder.decode(value), expect)

        value = '{"ISO8601_time": "23:59:59.123456"}'
        expect = datetime.time(23, 59, 59, 123456)
        self.assertEqual(decoder.decode(value), expect)

        value = '{"__decimal__": "59.123456"}'
        expect = Decimal("59.123456")
        self.assertEqual(decoder.decode(value), expect)

        value = '{"__deque__": []}'
        expect = deque()
        self.assertEqual(decoder.decode(value), expect)

        value = (
            '{"__class__": {"state": {"a": {"UUID": "6ba7b8119dad11d180b400c04'
            'fd430c8"}}, "topic": "eventsourcing.tests.test_transcoding#MyObje'
            'ctClass"}}'
        )
        expect = MyObjectClass(NAMESPACE_URL)
        self.assertEqual(decoder.decode(value), expect)

        value = '{"__tuple__": {"state": [1, 2, 4], "topic": "builtins#tuple"}}'
        expect = tuple([1, 2, 4])
        decoded = decoder.decode(value)
        self.assertEqual(decoded, expect)

        value = (
            '{"__tuple__": {"state": [1, "2", {"__class__": {"state": '
            '{"a": [3, "4"]}, "topic": "eventsourcing.tests.test_trans'
            'coding#MyObjectClass"}}], "topic": "eventsourcing.tests.t'
            'est_transcoding#MyNamedTuple"}}'
        )
        expect = MyNamedTuple(a=1, b="2", c=MyObjectClass([3, "4"]))
        decoded = decoder.decode(value)
        self.assertEqual(decoded, expect)

        if sys.version_info >= (3, 7):
            value = (
                '{"__class__": {"state": {"a": 1, "b": "2", "c": {'
                '"__decimal__": "3.0"}}, "topic": "eventsourcing.t'
                'ests.test_transcoding#MyDataClass"}}'
            )
            expected = MyDataClass(1, "2", Decimal("3.0"))
            self.assertEqual(decoder.decode(value), expected)

        # Check raises ValueError when JSON string is invalid.
        with self.assertRaises(ValueError):
            decoder.decode("{")

    def test_json_loads(self):
        # Check raises ValueError when JSON string is invalid.
        with self.assertRaises(ValueError):
            json_loads("{")


class MyObjectClass(object):
    def __init__(self, a):
        self.a = a

    def __eq__(self, other):
        return self.a == other.a

    def __ne__(self, other):
        return not self.__eq__(other)


MyNamedTuple = namedtuple("MyNamedTuple", field_names=["a", "b", "c"])


if sys.version_info >= (3, 7):
    @dataclass
    class MyDataClass(object):
        a: int
        b: str
        c: Decimal
