"""
The `rfc8785` APIs.
"""

__version__ = "0.0.1"

from ._impl import CanonicalizationError, FloatDomainError, IntegerDomainError, dump, dumps

__all__ = [
    "CanonicalizationError",
    "IntegerDomainError",
    "FloatDomainError",
    "dump",
    "dumps",
]
