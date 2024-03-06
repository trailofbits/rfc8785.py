# rfc8785

<!--- BADGES: START --->
[![CI](https://github.com/trailofbits/rfc8785/actions/workflows/tests.yml/badge.svg)](https://github.com/trailofbits/rfc8785/actions/workflows/tests.yml)
[![PyPI version](https://badge.fury.io/py/rfc8785.svg)](https://pypi.org/project/rfc8785)
[![Packaging status](https://repology.org/badge/tiny-repos/python:rfc8785.svg)](https://repology.org/project/python:rfc8785/versions)
<!--- BADGES: END --->

A pure-Python, no-dependency implementation of [RFC 8785], a.k.a. JSON Canonicalization Scheme or JCS.

This implementation should be behaviorally comparable to
[Andrew Rundgren's reference implementation], with the following added constraints:

1. This implementation does not transparently convert non-`str` dictionary keys into
   strings. Users must explicitly perform this conversion.
1. No support for indentation, pretty-printing, etc. is provided. The output is always
   minimally encoded.
2. All APIs produce UTF-8-encoded `bytes` objects or `bytes` I/O.

## Installation

```bash
python -m pip install rfc8785
```

## Usage

See the full API documentation [here].

```python
import rfc8785

foo = {
    "key": "value",
    "another-key": 2,
    "a-third": [1, 2, 3, [4], (5, 6, "this works too")],
    "more": [None, True, False],
}

rfc8785.dumps(foo)
```

yields:

```python
b'{"a-third":[1,2,3,[4],[5,6,"this works too"]],"another-key":2,"key":"value","more":[null,true,false]}'
```

For direct serialization to an I/O sink, use `rfc8785.dump` instead:

```python
import rfc8785

with open("/some/file", mode="wb") as io:
    rfc8785.dump([1, 2, 3, 4], io)
```

All APIs raise `rfc8785.CanonicalizationError` or a subclass on serialization failures.

## Licensing

Apache License, Version 2.0.

Where noted, parts of this implementation are adapted from [Andrew Rundgren's reference implementation], which is also licensed under the Apache License, Version 2.0.

[RFC 8785]: https://datatracker.ietf.org/doc/html/rfc8785

[Andrew Rundgren's reference implementation]: https://github.com/cyberphone/json-canonicalization/tree/master/python3

[here]: https://trailofbits.github.io/rfc8785.py
