from __future__ import annotations
from poker_equity.equity import equity_vs_range

def test_vs_range_reproducible():
    r1 = equity_vs_range("AhKh", "TT+,AQs+,KQo", iters=20_000, seed=123)
    r2 = equity_vs_range("AhKh", "TT+,AQs+,KQo", iters=20_000, seed=123)
    assert r1["hero"]["equity"] == r2["hero"]["equity"]
    assert r1["meta"]["range_size_available"] <= r1["meta"]["range_size"]

