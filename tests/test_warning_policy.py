from __future__ import annotations

import importlib
import sys
import warnings

from starlette.exceptions import StarletteDeprecationWarning


def test_fastapi_testclient_import_is_warning_free() -> None:
    sys.modules.pop("fastapi.testclient", None)
    sys.modules.pop("starlette.testclient", None)

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        module = importlib.import_module("fastapi.testclient")

    assert hasattr(module, "TestClient")
    assert not any(
        issubclass(warning.category, StarletteDeprecationWarning) for warning in captured
    )
