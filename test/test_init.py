"""Initial testing module."""

import json

import pytest

import rfc8785


def test_version() -> None:
    version = getattr(rfc8785, "__version__", None)
    assert version is not None
    assert isinstance(version, str)


@pytest.mark.parametrize("name", ["arrays", "french", "structures", "unicode", "values", "weird"])
def test_roundtrip(vector, name):
    input, output, outhex = vector(name)

    py_input = json.loads(input)

    # Each input, when canonicalized, matches the exact bytes expected.
    actual_output = rfc8785.dumps(py_input)
    assert output == actual_output == outhex

    actual_deserialized = json.loads(actual_output)
    assert actual_deserialized == py_input


def test_exception_hierarchy():
    assert issubclass(rfc8785.CanonicalizationError, ValueError)
    assert issubclass(rfc8785.IntegerDomainError, rfc8785.CanonicalizationError)
    assert issubclass(rfc8785.FloatDomainError, rfc8785.CanonicalizationError)
    assert not issubclass(rfc8785.IntegerDomainError, rfc8785.FloatDomainError)
    assert not issubclass(rfc8785.FloatDomainError, rfc8785.IntegerDomainError)
