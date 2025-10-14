from __future__ import annotations
from poker_equity.ranges import parse_range, filter_dead_combos

def _count(spec: str) -> int:
    return len(parse_range(spec))

def test_basic_counts():
    assert _count("TT") == 6
    assert _count("TT+") == 6*5  # TT,JJ,QQ,KK,AA
    assert _count("AKs") == 4
    assert _count("AKo") == 12
    assert _count("AK")  == 16
    assert _count("AQ+") == 16 + 16  # AQ + AK
    assert _count("AQs+") == 4 + 4   # AQs + AKs
    assert _count("A5s-A2s") == 4*4  # 4 rangs * 4 suited combos

def test_filter_dead_cards():
    combos = parse_range("AK")
    # Dead: As, Kh → cela supprime toutes combos contenant As ou Kh
    # Index carte: s*13+rank -> As=(s=0,r=12)=12 ; Kh=(s=?,r=11) pour toutes couleurs; on donne deux cartes spécifiques
    dead = [12, (1*13+11)]  # As, Kh♥
    rem = filter_dead_combos(combos, dead)
    assert len(rem) < len(combos)
    for c1, c2 in rem:
        assert c1 not in dead and c2 not in dead
