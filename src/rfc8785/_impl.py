"""
Internal implementation module for `rfc8785`.

This module is NOT a public API, and is not considered stable.
"""

from __future__ import annotations

import math
import re
import typing
from io import BytesIO

_Scalar = typing.Union[bool, int, str, float, None]

_Value = typing.Union[
    _Scalar,
    typing.Sequence["_Value"],
    typing.Tuple["_Value"],
    typing.Mapping[str, "_Value"],
]

_INT_MAX = 2**53 - 1
_INT_MIN = -(2**53) + 1

# These are adapted from Andrew Rundgren's reference implementation,
# which is licensed under the Apache License, version 2.0.
# See: <https://github.com/cyberphone/json-canonicalization/blob/ba74d44ecf5/python3/src/org/webpki/json/Canonicalize.py>
# See: <https://github.com/cyberphone/json-canonicalization/blob/ba74d44ecf5/python3/src/org/webpki/json/LICENSE>
_ESCAPE = re.compile(r'[\x00-\x1f\\"\b\f\n\r\t]')
_ESCAPE_DCT = {
    "\\": "\\\\",
    '"': '\\"',
    "\b": "\\b",
    "\f": "\\f",
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}
for i in range(0x20):
    _ESCAPE_DCT.setdefault(chr(i), f"\\u{i:04x}")


class CanonicalizationError(ValueError):
    """
    The base error for all errors during canonicalization.
    """

    pass


class IntegerDomainError(CanonicalizationError):
    """
    The given integer exceeds the true integer precision of an
    IEEE 754 double-precision float, which is what JSON uses.
    """

    def __init__(self, n: int) -> None:
        """
        Initialize an `IntegerDomainError`.
        """
        super().__init__(f"{n} exceeds safe integer domain for JSON floats")


class FloatDomainError(CanonicalizationError):
    """
    The given float cannot be represented in JCS, typically because it's
    infinite, NaN, or an invalid representation.
    """

    def __init__(self, f: float) -> None:
        """
        Initialize an `FloatDomainError`.
        """

        super().__init__(f"{f} is not representable in JCS")


def _serialize_str(s: str, sink: typing.IO[bytes]) -> None:
    """
    Serialize a string as a JSON string, per RFC 8785 3.2.2.2.
    """

    def _replace(match: re.Match) -> str:
        return _ESCAPE_DCT[match.group(0)]

    sink.write(b'"')
    try:
        # Encoding to UTF-8 means that we'll reject surrogates and other
        # non-UTF-8-isms.
        sink.write(_ESCAPE.sub(_replace, s).encode("utf-8"))
    except UnicodeEncodeError as e:
        raise CanonicalizationError("input contains non-UTF-8 codepoints") from e
    sink.write(b'"')


def _serialize_float(f: float, sink: typing.IO[bytes]) -> None:
    """
    Serialize a floating point number to a stable string format, as
    defined in ECMA 262 7.1.12.1 and amended by RFC 8785 3.2.2.3.
    """

    # NaN and infinite forms are prohibited.
    if math.isnan(f) or math.isinf(f):
        raise FloatDomainError(f)

    # Python does not distinguish between +0 and -0.
    if f == 0:
        sink.write(b"0")
        return

    # Negatives get serialized by prepending the sign marker and serializing
    # the positive form.
    if f < 0:
        sink.write(b"-")
        _serialize_float(-f, sink)
        return

    # The remainder of this implementation is adapted from
    # Andrew Rundgren's reference implementation.

    # Now we should only have valid non-zero values
    stringified = str(f)

    exponent_str = ""
    exponent_value = 0
    q = stringified.find("e")
    if q > 0:
        # Grab the exponent and remove it from the number
        exponent_str = stringified[q:]
        if exponent_str[2:3] == "0":
            # Suppress leading zero on exponents
            exponent_str = exponent_str[:2] + exponent_str[3:]
        stringified = stringified[0:q]
        exponent_value = int(exponent_str[1:])

    # Split number in first + dot + last
    first = stringified
    dot = ""
    last = ""
    q = stringified.find(".")
    if q > 0:
        dot = "."
        first = stringified[:q]
        last = stringified[q + 1 :]

    # Now the string is split into: first + dot + last + exponent_str
    if last == "0":
        # Always remove trailing .0
        dot = ""
        last = ""

    if exponent_value > 0 and exponent_value < 21:
        # Integers are shown as is with up to 21 digits
        first += last
        last = ""
        dot = ""
        exponent_str = ""
        q = exponent_value - len(first)
        while q >= 0:
            q -= 1
            first += "0"
    elif exponent_value < 0 and exponent_value > -7:
        # Small numbers are shown as 0.etc with e-6 as lower limit
        last = first + last
        first = "0"
        dot = "."
        exponent_str = ""
        q = exponent_value
        while q < -1:
            q += 1
            last = "0" + last

    sink.write(f"{first}{dot}{last}{exponent_str}".encode())


def dumps(obj: _Value) -> bytes:
    """
    Perform JCS serialization of `obj`, returning the canonical serialization
    as `bytes`.
    """
    # TODO: Optimize this?
    sink = BytesIO()
    dump(obj, sink)
    return sink.getvalue()


def dump(obj: _Value, sink: typing.IO[bytes]) -> None:
    """
    Perform JCS serialization of `obj` into `sink`.
    """

    if obj is None:
        sink.write(b"null")
    elif isinstance(obj, bool):
        obj = bool(obj)
        if obj is True:
            sink.write(b"true")
        else:
            sink.write(b"false")
    elif isinstance(obj, int):
        obj = int(obj)
        if obj < _INT_MIN or obj > _INT_MAX:
            raise IntegerDomainError(obj)
        sink.write(str(obj).encode("utf-8"))
    elif isinstance(obj, str):
        # NOTE: We don't coerce with `str(...)`` here, since that will do
        # the wrong thing for `(str, Enum)` subtypes where `__str__` is
        # `Enum.__str__`.
        _serialize_str(obj, sink)
    elif isinstance(obj, float):
        obj = float(obj)
        _serialize_float(obj, sink)
    elif isinstance(obj, (list, tuple)):
        obj = list(obj)
        if not obj:
            # Optimization for empty lists.
            sink.write(b"[]")
            return

        sink.write(b"[")
        for idx, elem in enumerate(obj):
            if idx > 0:
                sink.write(b",")
            dump(elem, sink)
        sink.write(b"]")
    elif isinstance(obj, dict):
        obj = dict(obj)
        if not obj:
            # Optimization for empty dicts.
            sink.write(b"{}")
            return

        # RFC 8785 3.2.3: Objects are sorted by key; keys are ordered
        # by their UTF-16 encoding. The spec isn't clear about which endianness,
        # but the examples imply that the big endian encoding is used.
        try:
            obj_sorted = sorted(obj.items(), key=lambda kv: kv[0].encode("utf-16be"))
        except AttributeError:
            # Failing to call `encode()` indicates that a key isn't a string.
            raise CanonicalizationError("object keys must be strings")

        sink.write(b"{")
        for idx, (key, value) in enumerate(obj_sorted):
            if idx > 0:
                sink.write(b",")

            _serialize_str(key, sink)
            sink.write(b":")
            dump(value, sink)

        sink.write(b"}")
    else:
        raise CanonicalizationError(f"unsupported type: {type(obj)}")
