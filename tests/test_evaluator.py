from __future__ import annotations
from poker_equity.evaluator import evaluate7

# Utilitaire: construire rapidement une carte suit*13 + rank (2..A)
def C(rank_char: str, suit_char: str) -> int:
    ranks = "23456789TJQKA"
    suits = "shdc"  # spades=0, hearts=1, diamonds=2, clubs=3
    r = ranks.index(rank_char.upper())
    s = suits.index(suit_char.lower())
    return s * 13 + r

def test_rank_ordering_simple():
    # Quinte flush > Carré > Full > Flush > Straight > Trips > TwoPair > Pair > High
    straight_flush = [C("9","s"), C("T","s"), C("J","s"), C("Q","s"), C("K","s"), C("2","h"), C("3","d")]
    quads          = [C("K","s"), C("K","h"), C("K","d"), C("K","c"), C("2","s"), C("3","h"), C("4","d")]
    full_house     = [C("Q","s"), C("Q","h"), C("Q","d"), C("2","s"), C("2","h"), C("3","d"), C("4","c")]
    flush_cards    = [C("A","h"), C("J","h"), C("9","h"), C("5","h"), C("2","h"), C("3","d"), C("4","c")]
    straight_cards = [C("9","s"), C("T","h"), C("J","d"), C("Q","c"), C("K","s"), C("2","h"), C("3","d")]
    trips_cards    = [C("J","s"), C("J","h"), C("J","d"), C("A","c"), C("9","s"), C("2","h"), C("3","d")]
    two_pair       = [C("T","s"), C("T","h"), C("9","d"), C("9","c"), C("A","s"), C("2","h"), C("3","d")]
    pair_cards     = [C("A","s"), C("A","h"), C("Q","d"), C("9","c"), C("3","s"), C("2","h"), C("4","d")]
    high_cards     = [C("A","s"), C("Q","h"), C("9","d"), C("7","c"), C("5","s"), C("3","h"), C("2","d")]

    s_sf = evaluate7(straight_flush)
    s_4k = evaluate7(quads)
    s_fh = evaluate7(full_house)
    s_f  = evaluate7(flush_cards)
    s_st = evaluate7(straight_cards)
    s_3k = evaluate7(trips_cards)
    s_2p = evaluate7(two_pair)
    s_1p = evaluate7(pair_cards)
    s_h  = evaluate7(high_cards)

    assert s_sf > s_4k > s_fh > s_f > s_st > s_3k > s_2p > s_1p > s_h

def test_wheel_straight_and_normal_straight():
    # Roue A-2-3-4-5 vs 6-high straight
    wheel7 = [C("A","s"), C("5","h"), C("4","d"), C("3","c"), C("2","s"), C("K","h"), C("Q","d")]
    six_hi = [C("6","s"), C("5","h"), C("4","d"), C("3","c"), C("2","s"), C("K","h"), C("Q","d")]
    assert evaluate7(six_hi) > evaluate7(wheel7)
