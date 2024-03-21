"""
Internal implementation tests.
"""

import gzip
import json
import struct
import sys
from enum import Enum, IntEnum
from io import BytesIO

import pytest
import rfc8785._impl as impl


@pytest.mark.parametrize(
    ("hex_ieee", "expected"),
    [
        # hex_ieee is the raw 64-bit IEEE 754 float, in big-endian order.
        ("0000000000000000", b"0"),
        ("8000000000000000", b"0"),
        ("0000000000000001", b"5e-324"),
        ("8000000000000001", b"-5e-324"),
        ("7fefffffffffffff", b"1.7976931348623157e+308"),
        ("ffefffffffffffff", b"-1.7976931348623157e+308"),
        ("4340000000000000", b"9007199254740992"),
        ("c340000000000000", b"-9007199254740992"),
        ("4430000000000000", b"295147905179352830000"),
        ("7fffffffffffffff", None),
        ("7ff0000000000000", None),
        ("44b52d02c7e14af5", b"9.999999999999997e+22"),
        ("44b52d02c7e14af6", b"1e+23"),
        ("44b52d02c7e14af7", b"1.0000000000000001e+23"),
        ("444b1ae4d6e2ef4e", b"999999999999999700000"),
        ("444b1ae4d6e2ef4f", b"999999999999999900000"),
        ("444b1ae4d6e2ef50", b"1e+21"),
        ("3eb0c6f7a0b5ed8c", b"9.999999999999997e-7"),
        ("3eb0c6f7a0b5ed8d", b"0.000001"),
        ("41b3de4355555553", b"333333333.3333332"),
        ("41b3de4355555554", b"333333333.33333325"),
        ("41b3de4355555555", b"333333333.3333333"),
        ("41b3de4355555556", b"333333333.3333334"),
        ("41b3de4355555557", b"333333333.33333343"),
        ("becbf647612f3696", b"-0.0000033333333333333333"),
        ("43143ff3c1cb0959", b"1424953923781206.2"),
    ],
)
def test_es6_float_stringification(hex_ieee, expected):
    bytes_ieee = bytearray.fromhex(hex_ieee)
    (float_ieee,) = struct.unpack(">d", bytes_ieee)

    sink = BytesIO()
    if expected is None:
        with pytest.raises(impl.FloatDomainError):
            impl._serialize_float(float_ieee, sink)
    else:
        impl._serialize_float(float_ieee, sink)
        actual = sink.getvalue()
        assert actual == expected


def test_es6_float_stringification_full(es6_test_file):
    if not es6_test_file.is_file():
        pytest.skip(f"no {es6_test_file}, skipping")

    # TODO: Thread or otherwise chunk this; it's ridiculously slow for
    # 100M testcases.
    with gzip.open(es6_test_file, mode="rt") as io:
        for line in io:
            line = line.rstrip()
            hex_ieee, expected = line.split(",", 1)
            # `hex_ieee` is not consistently padded, so we have to do
            # things the annoying way: convert it into an int, pack the int
            # as u64be, and then unpack into a float64be.
            (float_ieee,) = struct.unpack(">d", struct.pack(">Q", int(hex_ieee, 16)))

            sink = BytesIO()
            impl._serialize_float(float_ieee, sink)

            actual = sink.getvalue().decode()
            assert actual == expected


def test_integer_domain():
    impl.dumps(impl._INT_MAX)
    with pytest.raises(impl.IntegerDomainError):
        impl.dumps(impl._INT_MAX + 1)

    impl.dumps(impl._INT_MIN)
    with pytest.raises(impl.IntegerDomainError):
        impl.dumps(impl._INT_MIN - 1)


def test_string_invalid_utf8():
    # escaped surrogate is fine
    impl.dumps("\\udead")
    with pytest.raises(impl.CanonicalizationError):
        impl.dumps("\udead")


def test_dumps_invalid_type():
    with pytest.raises(impl.CanonicalizationError):
        # set is not serializable
        impl.dumps({1, 2, 3})


def test_dumps_intenum():
    # IntEnum is a subclass of int, so this should work transparently.
    class X(IntEnum):
        A = 1
        B = 2
        C = 9001

    raw = impl.dumps([X.A, X.B, X.C])
    assert json.loads(raw) == [1, 2, 9001]


@pytest.mark.skipif(sys.version_info < (3, 11), reason="StrEnum added in 3.11+")
def test_dumps_strenum():
    from enum import StrEnum

    # StrEnum is a subclass of str, so this should work transparently.
    class X(StrEnum):
        A = "foo"
        B = "bar"
        C = "baz"

    raw = impl.dumps([X.A, X.B, X.C])
    assert json.loads(raw) == ["foo", "bar", "baz"]


def test_dumps_enum_multiple_inheritance():
    # Manually inheriting str, Enum should also work.
    class X(str, Enum):
        A = "foo"
        B = "bar"
        C = "baz"

    raw = impl.dumps([X.A, X.B, X.C])
    assert json.loads(raw) == ["foo", "bar", "baz"]

    # Same for other JSON-able enum types.
    class Y(dict, Enum):
        A = {"A": "foo"}
        B = {"B": "bar"}
        C = {"C": "baz"}

    raw = impl.dumps([Y.A, Y.B, Y.C])
    assert json.loads(raw) == [{"A": "foo"}, {"B": "bar"}, {"C": "baz"}]

    class Z(int, Enum):
        A = 1
        B = 2
        C = 3

    raw = impl.dumps([Z.A, Z.B, Z.C])
    assert json.loads(raw) == [1, 2, 3]


def test_dumps_bare_enum_fails():
    class X(Enum):
        A = "1"
        B = 2
        C = 3.0

    # Python's json doesn't allow this, so we don't either.
    with pytest.raises(impl.CanonicalizationError, match="unsupported type"):
        impl.dumps([X.A, X.B, X.C])


def test_dumps_nonstring_key():
    with pytest.raises(impl.CanonicalizationError, match="object keys must be strings"):
        impl.dumps({1: 2, None: 3})
