from __future__ import annotations
import importlib

def test_import_package():
    m = importlib.import_module("poker_equity")
    assert hasattr(m, "__version__")
