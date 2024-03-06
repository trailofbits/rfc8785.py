from collections.abc import Callable
from pathlib import Path

import pytest

_ASSETS = Path(__file__).parent / "assets"
assert _ASSETS.is_dir()


@pytest.fixture
def vector() -> Callable[[str], tuple[bytes, bytes, bytes]]:
    def _vector(name: str) -> tuple[bytes, bytes, bytes]:
        input = _ASSETS / f"input/{name}.json"
        output = _ASSETS / f"output/{name}.json"
        outhex = _ASSETS / f"outhex/{name}.txt"

        return (input.read_bytes(), output.read_bytes(), bytearray.fromhex(outhex.read_text()))

    return _vector


@pytest.fixture
def es6_test_file() -> Path:
    return _ASSETS / "es6testfile100m.txt.gz"
