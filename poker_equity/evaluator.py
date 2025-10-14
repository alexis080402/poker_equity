from __future__ import annotations

from itertools import combinations
from typing import Iterable, List, Sequence, Tuple

# Catégories (ordre croissant → plus petit = plus faible)
# 0: High Card, 1: Pair, 2: Two Pair, 3: Trips, 4: Straight,
# 5: Flush, 6: Full House, 7: Quads, 8: Straight Flush
_HAND_RANK_NAMES = [
    "HighCard", "Pair", "TwoPair", "Trips",
    "Straight", "Flush", "FullHouse", "Quads", "StraightFlush",
]

RANKS_STR = "23456789TJQKA"  # 0..12
# Helpers rangs/couleurs
def _rank(card: int) -> int:  # 0..12
    return card % 13
def _suit(card: int) -> int:  # 0..3
    return card // 13

def _is_straight(sorted_unique_ranks_desc: List[int]) -> Tuple[bool, int]:
    """Détecte une quinte et renvoie (ok, high_rank). Gère la roue A-2-3-4-5."""
    # Cas roue: A=12, 3,2,1,0 présents
    ranks = sorted_unique_ranks_desc
    # Sliding window
    for i in range(len(ranks) - 4 + 1):
        window = ranks[i:i+5]
        # Si l'écart max-min == 4 et 5 uniques consécutifs
        if window[0] - window[-1] == 4 and len(window) == 5:
            # Vérifier consécutivité stricte
            ok = all(window[j] - 1 == window[j+1] for j in range(4))
            if ok:
                return True, window[0]
    # Roue explicite : A,5,4,3,2 -> ranks contiennent {12, 3,2,1,0}
    wheel = {12, 3, 2, 1, 0}
    if wheel.issubset(set(ranks)):
        return True, 3  # high=5 (rank=3)
    return False, -1

def _evaluate5(cards5: Sequence[int]) -> Tuple[int, Tuple[int, ...]]:
    """Classe une main 5 cartes. Retourne (catégorie, tiebreakers...). Plus grand = meilleur.
    Conventions: ranks 0..12 (A=12), suits 0..3. Tiebreakers en ordre lexicographique.
    """
    rs = sorted([_rank(c) for c in cards5], reverse=True)
    ss = [_suit(c) for c in cards5]

    # Comptes par rang
    counts = {}
    for r in rs:
        counts[r] = counts.get(r, 0) + 1
    # Tri par (count desc, rank desc)
    groups = sorted(((cnt, r) for r, cnt in counts.items()), key=lambda x: (x[0], x[1]), reverse=True)
    is_flush = len({*ss}) == 1

    # Straight: travailler sur ranks uniques, desc
    uniq_desc = sorted(set(rs), reverse=True)
    is_straight, straight_high = _is_straight(uniq_desc)

    if is_straight and is_flush:
        # Straight flush; pour la roue A-2-3-4-5, high=3 (rank du 5)
        return 8, (straight_high,)

    # Quads / Full
    if groups[0][0] == 4:
        # (7, [rank_quads, kicker])
        quad_rank = groups[0][1]
        kicker = max([r for r in rs if r != quad_rank])
        return 7, (quad_rank, kicker)

    if groups[0][0] == 3 and len(groups) >= 2 and groups[1][0] >= 2:
        # Full house: (6, [rank_trips, rank_pair])
        trips = groups[0][1]
        pair = max(r for (cnt, r) in groups[1:] if cnt >= 2)
        return 6, (trips, pair)

    if is_flush:
        # Flush: (5, top5 ranks desc)
        return 5, tuple(rs)

    if is_straight:
        # Straight: (4, high)
        return 4, (straight_high,)

    if groups[0][0] == 3:
        # Trips: (3, [rank_trips, kickers desc])
        trips = groups[0][1]
        kickers = sorted([r for r in rs if r != trips], reverse=True)[:2]
        return 3, (trips, *kickers)

    if groups[0][0] == 2 and len(groups) >= 2 and groups[1][0] == 2:
        # Double paire: (2, [max_pair, min_pair, kicker])
        pairs = sorted([r for (cnt, r) in groups if cnt == 2], reverse=True)
        kicker = max([r for r in rs if r not in pairs])
        return 2, (pairs[0], pairs[1], kicker)

    if groups[0][0] == 2:
        # Paire simple: (1, [pair_rank, kickers desc])
        pair = groups[0][1]
        kickers = [r for r in rs if r != pair][:3]
        return 1, (pair, *kickers)

    # High card: (0, ranks desc)
    return 0, tuple(rs)

def evaluate7(cards7: Sequence[int]) -> Tuple[int, Tuple[int, ...]]:
    """Évalue 7 cartes → meilleur score 5 cartes. Retourne un tuple comparable.
    Convention: plus grand tuple = meilleure main.
    """
    assert len(cards7) == 7, "evaluate7 attend exactement 7 cartes"
    best = (-1, ())  # plus petit que toute vraie main
    for comb in combinations(cards7, 5):
        score = _evaluate5(comb)
        if score > best:
            best = score
    return best

def describe_score(score: Tuple[int, Tuple[int, ...]]) -> str:
    """Optionnel: description lisible d'un score (utile pour debug/affichage)."""
    cat, tb = score
    name = _HAND_RANK_NAMES[cat]
    return f"{name} {tb}"
