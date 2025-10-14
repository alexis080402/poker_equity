from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple

from .cards import parse_combo, parse_board, deck_without
from .evaluator import evaluate7
from .ranges import parse_range, filter_dead_combos


def equity_hu(hero: str, villain: str, board: str | None = None,
              iters: int = 200_000, seed: int | None = None) -> dict:
    """Calcul d'equity HU par Monte Carlo (main connue vs main connue)."""
    h1, h2 = parse_combo(hero)
    v1, v2 = parse_combo(villain)
    board_cards = parse_board(board)

    known = [h1, h2, v1, v2, *board_cards]
    deck = deck_without(known)

    # ----- Cas déterministe : board complet -----
    if len(board_cards) == 5:
        s_hero = evaluate7([h1, h2, *board_cards])
        s_vil  = evaluate7([v1, v2, *board_cards])
        if s_hero > s_vil:
            p = 1.0
        elif s_hero < s_vil:
            p = 0.0
        else:
            p = 0.5
        stdev = 0.0
        z = 1.96
        ci_low = p
        ci_high = p
        return {
            "hero":    {"equity": p,       "stdev": stdev, "ci95": [ci_low, ci_high], "n": 1},
            "villain": {"equity": 1 - p,   "stdev": stdev, "ci95": [1-p, 1-p],        "n": 1},
            "meta":    {"hero": hero, "villain": villain, "board": board or "", "seed": seed},
        }

    # ----- Cas Monte Carlo -----
    rng = random.Random(seed)
    need = 5 - len(board_cards)
    wins = ties = 0

    for _ in range(iters):
        draw = rng.sample(deck, need)
        full_board = board_cards + draw
        s_hero = evaluate7([h1, h2, *full_board])
        s_vil  = evaluate7([v1, v2, *full_board])
        if s_hero > s_vil:
            wins += 1
        elif s_hero == s_vil:
            ties += 1

    p = (wins + 0.5 * ties) / iters
    stdev = math.sqrt(max(p * (1 - p) / iters, 0.0))
    z = 1.96
    ci_low = max(p - z * stdev, 0.0)
    ci_high = min(p + z * stdev, 1.0)

    return {
        "hero":    {"equity": p,       "stdev": stdev, "ci95": [ci_low, ci_high], "n": iters},
        "villain": {"equity": 1 - p,   "stdev": stdev, "ci95": [1-ci_high, 1-ci_low], "n": iters},
        "meta":    {"hero": hero, "villain": villain, "board": board or "", "seed": seed},
    }


def equity_vs_range(hero: str, villain_range: str, board: str | None = None,
                    iters: int = 200_000, seed: int | None = None) -> dict:
    """Equity de Héro (main connue) vs une range Vilain (texte). Monte Carlo uniforme sur les combos de la range."""
    h1, h2 = parse_combo(hero)
    board_cards = parse_board(board)

    # Expand range & filtre des dead cards (héros + board connus)
    raw = parse_range(villain_range)
    avail = filter_dead_combos(raw, dead=[h1, h2, *board_cards])
    if not avail:
        raise ValueError("Range vide après retrait des cartes mortes (héros/board).")

    deck0 = deck_without([h1, h2, *board_cards])
    need = 5 - len(board_cards)

    # Cas déterministe (board complet) → énumération sur combos de la range
    if need == 0:
        wins = ties = 0
        for v1, v2 in avail:
            s_h = evaluate7([h1, h2, *board_cards])
            s_v = evaluate7([v1, v2, *board_cards])
            if s_h > s_v:
                wins += 1
            elif s_h == s_v:
                ties += 1
        p = (wins + 0.5 * ties) / len(avail)
        stdev = 0.0
        return {
            "hero":    {"equity": p, "stdev": stdev, "ci95": [p, p], "n": len(avail)},
            "villain": {"equity": 1 - p, "stdev": stdev, "ci95": [1 - p, 1 - p], "n": len(avail)},
            "meta":    {"hero": hero, "villain_range": villain_range, "board": board or "",
                        "seed": None, "range_size": len(raw), "range_size_available": len(avail)},
        }

    rng = random.Random(seed)
    wins = ties = 0

    for _ in range(iters):
        # Échantillonne un combo Vilain disponible
        v1, v2 = rng.choice(avail)  # uniforme sur la range filtrée

        # Deck pour tirage du board manquant : retirer aussi v1,v2
        deck = [c for c in deck0 if c != v1 and c != v2]
        draw = rng.sample(deck, need)
        full_board = board_cards + draw

        s_h = evaluate7([h1, h2, *full_board])
        s_v = evaluate7([v1, v2, *full_board])

        if s_h > s_v:
            wins += 1
        elif s_h == s_v:
            ties += 1

    p = (wins + 0.5 * ties) / iters
    stdev = math.sqrt(max(p * (1 - p) / iters, 0.0))
    z = 1.96
    lo, hi = max(p - z * stdev, 0.0), min(p + z * stdev, 1.0)

    return {
        "hero":    {"equity": p, "stdev": stdev, "ci95": [lo, hi], "n": iters},
        "villain": {"equity": 1 - p, "stdev": stdev, "ci95": [1 - hi, 1 - lo], "n": iters},
        "meta":    {"hero": hero, "villain_range": villain_range, "board": board or "",
                    "seed": seed, "range_size": len(raw), "range_size_available": len(avail)},
    }
