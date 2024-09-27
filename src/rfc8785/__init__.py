"""
The `rfc8785` APIs.

See [RFC 8785](https://datatracker.ietf.org/doc/html/rfc8785) for a full
definition of the JSON Canonicalization Scheme.

## Quick start

```python
import rfc8785

rfc8785.dumps({"anything that can be json serialized": "here"})
```
"""

__version__ = "0.1.4"

from ._impl import CanonicalizationError, FloatDomainError, IntegerDomainError, dump, dumps

__all__ = [
    "CanonicalizationError",
    "IntegerDomainError",
    "FloatDomainError",
    "dump",
    "dumps",
]
