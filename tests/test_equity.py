# tests/test_equity.py
from __future__ import annotations
from poker_equity.equity import equity_hu

def test_equity_deterministic_river():
    # Hero: AsAh ; Villain: KdKh ; Board: Ad Ks 2c 9d 9h
    # → Hero = Aces full of Nines ; Villain = Kings full of Nines → Hero gagne
    res = equity_hu("AsAh", "KdKh", board="AdKs2c9d9h")
    assert res["hero"]["n"] == 1
    assert res["hero"]["equity"] == 1.0
    assert res["villain"]["equity"] == 0.0

def test_equity_mc_seed_reproducible():
    r1 = equity_hu("AhKh", "QdQs", board=None, iters=50_000, seed=123)
    r2 = equity_hu("AhKh", "QdQs", board=None, iters=50_000, seed=123)
    assert r1["hero"]["equity"] == r2["hero"]["equity"]
    assert r1["villain"]["equity"] == r2["villain"]["equity"]
