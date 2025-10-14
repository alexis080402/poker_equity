from __future__ import annotations
from typing import Iterable, List, Sequence, Set, Tuple
import re

# Conventions rangs/couleurs alignées avec cards.py
_RANKS = "23456789TJQKA"
_SUITS = "shdc"  # ♠=s=0, ♥=h=1, ♦=d=2, ♣=c=3

def _rank_idx(rc: str) -> int:
    return _RANKS.index(rc.upper())

def _card(rank_idx: int, suit_idx: int) -> int:
    # suit*13 + rank
    return suit_idx * 13 + rank_idx

def _is_pair(spec_hi: str, spec_lo: str) -> bool:
    return spec_hi.upper() == spec_lo.upper()

def _all_pair_combos(r: int) -> Set[Tuple[int, int]]:
    # C(4,2)=6 combinaisons pour la paire (r,r) sur 4 couleurs
    cards = [_card(r, s) for s in range(4)]
    combos: Set[Tuple[int, int]] = set()
    for i in range(4):
        for j in range(i + 1, 4):
            c1, c2 = cards[i], cards[j]
            combos.add(tuple(sorted((c1, c2))))
    return combos

def _all_suited_combos(r_hi: int, r_lo: int) -> Set[Tuple[int, int]]:
    # 4 combos (même couleur)
    combos: Set[Tuple[int, int]] = set()
    for s in range(4):
        c1 = _card(r_hi, s)
        c2 = _card(r_lo, s)
        combos.add(tuple(sorted((c1, c2))))
    return combos

def _all_offsuit_combos(r_hi: int, r_lo: int) -> Set[Tuple[int, int]]:
    # 12 combos offsuit = 16 totaux - 4 suited
    combos: Set[Tuple[int, int]] = set()
    for s1 in range(4):
        for s2 in range(4):
            if s1 == s2:
                continue
            c1 = _card(r_hi, s1)
            c2 = _card(r_lo, s2)
            combos.add(tuple(sorted((c1, c2))))
    return combos

def _all_both_combos(r_hi: int, r_lo: int) -> Set[Tuple[int, int]]:
    # 16 combos : 4 suited + 12 offsuit
    return _all_suited_combos(r_hi, r_lo) | _all_offsuit_combos(r_hi, r_lo)

_TOKEN = re.compile(
    r"""
    ^\s*
    (?P<hi>[2-9TJQKA])
    (?P<lo>[2-9TJQKA])?
    (?P<so>[so])?
    (?P<plus>\+)?
    \s*$
    """,
    re.VERBOSE | re.IGNORECASE,
)

def _expand_simple_token(hi: str, lo: str | None, so: str | None, plus: bool) -> Set[Tuple[int, int]]:
    hi_i = _rank_idx(hi)
    if lo is None:
        # Paires avec '+': ex "TT+"  (hi==lo implicite)
        lo_i = hi_i
        is_pair = True
    else:
        lo_i = _rank_idx(lo)
        is_pair = (hi.upper() == lo.upper())
        # Normaliser hi>lo pour non-paires
        if not is_pair and hi_i < lo_i:
            hi_i, lo_i = lo_i, hi_i

    combos: Set[Tuple[int, int]] = set()

    if is_pair:
        # "TT" ou "TT+"
        start = hi_i
        stop = _rank_idx("A")
        for r in range(start, stop + 1) if plus else [start]:
            combos |= _all_pair_combos(r)
        return combos

    # Non-paires : "AQ", "AQs", "AQo", avec/ sans '+'
    def add_nonpair(h: int, l: int):
        nonlocal combos, so
        if so is None:
            combos |= _all_both_combos(h, l)
        elif so.lower() == "s":
            combos |= _all_suited_combos(h, l)
        else:
            combos |= _all_offsuit_combos(h, l)

    if plus:
        # "AQ+" → AQ, AK  (même contrainte s/o)
        for h in range(hi_i, _rank_idx("A") + 1):
            if h == lo_i:
                continue
            add_nonpair(h, lo_i)
    else:
        add_nonpair(hi_i, lo_i)

    return combos

def _expand_dash_range(token: str) -> Set[Tuple[int, int]]:
    # Ex: "A5s-A2s" ; même hi et même s/o; on fait varier le 'lo' entre bornes
    # Forme attendue: Xys - Xzs  (y..z sont rangs, s/o identiques)
    left, right = [t.strip() for t in token.split("-", 1)]
    m1 = _TOKEN.match(left)
    m2 = _TOKEN.match(right)
    if not m1 or not m2:
        raise ValueError(f"Range invalide: {token!r}")
    hi1, lo1, so1, plus1 = m1.group("hi"), m1.group("lo"), m1.group("so"), m1.group("plus")
    hi2, lo2, so2, plus2 = m2.group("hi"), m2.group("lo"), m2.group("so"), m2.group("plus")

    if plus1 or plus2:
        raise ValueError(f"Le suffixe '+' est incompatible avec un intervalle: {token!r}")
    if lo1 is None or lo2 is None:
        raise ValueError(f"Intervalle non pair sans 'lo' explicite: {token!r}")

    # Pour non-paires on exige même hi et même so (s/o/None)
    if hi1.upper() != hi2.upper():
        raise ValueError(f"Intervalle avec hi différents: {token!r}")
    if (so1 or "").lower() != (so2 or "").lower():
        raise ValueError(f"Intervalle avec s/o incompatibles: {token!r}")

    hi_i = _rank_idx(hi1)
    l1 = _rank_idx(lo1)
    l2 = _rank_idx(lo2)
    # Normaliser sens
    lo_start, lo_stop = sorted((l1, l2), reverse=True)  # ex 5 -> 2

    combos: Set[Tuple[int, int]] = set()
    for l in range(lo_start, lo_stop - 1, -1):
        combos |= _expand_simple_token(hi1, _RANKS[l], so1, plus=False)
    return combos

def parse_range(text: str) -> Set[Tuple[int, int]]:
    """Parse une range en ensemble de combos (tuples (c1,c2) triés)."""
    if not text or not text.strip():
        raise ValueError("Range vide")
    parts = [p.strip() for p in re.split(r"[,\s]+", text) if p.strip()]
    combos: Set[Tuple[int, int]] = set()
    for p in parts:
        if "-" in p:
            combos |= _expand_dash_range(p)
        else:
            m = _TOKEN.match(p)
            if not m:
                raise ValueError(f"Token de range invalide: {p!r}")
            combos |= _expand_simple_token(
                m.group("hi"),
                m.group("lo"),
                m.group("so"),
                bool(m.group("plus")),
            )
    return combos

def filter_dead_combos(combos: Iterable[Tuple[int, int]], dead: Iterable[int]) -> List[Tuple[int, int]]:
    """Retire les combos contenant des cartes mortes."""
    dead_set = set(dead)
    out: List[Tuple[int, int]] = []
    for c1, c2 in combos:
        if c1 not in dead_set and c2 not in dead_set and c1 != c2:
            out.append((min(c1, c2), max(c1, c2)))
    return out
