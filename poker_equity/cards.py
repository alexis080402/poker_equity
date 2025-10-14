"""Parsing et normalisation des cartes/mains pour Texas Hold'em (HU).

Conventions d'encodage
----------------------
- Chaque carte est encodée sur un entier [0..51].
- Ordre des couleurs (suits): spades ♠=0, hearts ♥=1, diamonds ♦=2, clubs ♣=3.
- Ordre des rangs (ranks): '2'=0, ..., 'T'=8, 'J'=9, 'Q'=10, 'K'=11, 'A'=12.
- Index = suit * 13 + rank.

Entrées acceptées
-----------------
- Rangs: 2-9, T(=10), J, Q, K, A (insensibles à la casse; "10" est converti en "T").
- Couleurs: s,h,d,c ou symboles Unicode: ♠,♥,♦,♣ (insensibles à la casse).
- Mains/combo: "AhKh", "ah kh", "AH-KH", etc. Board: "AsKs2c" ou "As Ks 2c".

Erreurs levées
--------------
- CardParseError: format invalide, rang/couleur inconnus, doublons.
"""
from __future__ import annotations

import re
from typing import Iterable, List, Sequence, Tuple

__all__ = [
    "CardParseError",
    "parse_card",
    "parse_combo",
    "parse_board",
    "card_to_str",
    "deck52",
    "deck_without",
    "ensure_no_duplicates",
]


class CardParseError(ValueError):
    """Erreur de parsing/validation des cartes."""


# Mapping rangs et couleurs
_RANKS = {c: i for i, c in enumerate("23456789TJQKA")}
_SUITS = {"S": 0, "H": 1, "D": 2, "C": 3}

# Alias Unicode / textes
_UNICODE_TO_SUIT = {
    "♠": "S",
    "♣": "C",
    "♥": "H",
    "♦": "D",
}

# Token regex: capture paires (rank,suit) robustes
# - Rank: 10|[2-9TJQKA] (insensible casse)
# - Suit: [shdc] ou Unicode parmi ♠♥♦♣
_TOKEN = re.compile(r"(?i)\b(10|[2-9TJQKA])\s*([shdc]|[♠♥♦♣])\b")


# =========================
# Helpers de normalisation
# =========================

def _norm_rank(rank: str) -> str:
    r = rank.upper()
    if r == "10":
        r = "T"
    if r not in _RANKS:
        raise CardParseError(f"Rang invalide: {rank!r}")
    return r


def _norm_suit(suit: str) -> str:
    s = suit
    if s in _UNICODE_TO_SUIT:
        s = _UNICODE_TO_SUIT[s]
    s = s.upper()
    if s not in _SUITS:
        raise CardParseError(f"Couleur invalide: {suit!r}")
    return s


def card_to_str(card: int) -> str:
    """Retourne une représentation canonique 'Rs' (ex: 'Ah')."""
    if not (0 <= card <= 51):
        raise CardParseError(f"Index carte hors bornes: {card}")
    rank_i = card % 13
    suit_i = card // 13
    rank_c = "23456789TJQKA"[rank_i]
    suit_c = "shdc"[suit_i]
    return f"{rank_c}{suit_c}"


# =========================
# Parsing de cartes et mains
# =========================

def parse_card(text: str) -> int:
    """Parse une seule carte (ex: 'Ah', 'aH', 'A♥', '10c').

    Retourne un entier [0..51].
    """
    text = text.strip()
    m = _TOKEN.fullmatch(text)
    if not m:
        # Essai: format compact sans séparateur (ex 'Ah' ou '10c')
        if len(text) in (2, 3):
            rank_raw = text[:-1]
            suit_raw = text[-1]
            r = _norm_rank(rank_raw)
            s = _norm_suit(suit_raw)
        else:
            raise CardParseError(f"Carte invalide: {text!r}")
    else:
        r = _norm_rank(m.group(1))
        s = _norm_suit(m.group(2))

    rank_i = _RANKS[r]
    suit_i = _SUITS[s]
    return suit_i * 13 + rank_i


def _tokenize_cards(blob: str) -> List[str]:
    """Extrait toutes les cartes canoniques 'Rs' d'une chaîne.

    Accepte des séparateurs variés: espaces, virgules, tirets, etc.
    """
    tokens: List[str] = []
    blob = blob.strip()
    # 1) Extraction par regex
    for m in _TOKEN.finditer(blob):
        r = _norm_rank(m.group(1))
        s = _norm_suit(m.group(2))
        tokens.append(r + s.lower())
    # 2) Fallback: format compact sans séparateur: ex 'AsKs2c'
    if not tokens and blob:
        j = 0
        while j < len(blob):
            # rank peut être '10' (2 chars) ou 1 char
            if blob[j:j+2].lower() == "10":
                if j + 2 >= len(blob):
                    raise CardParseError("Chaîne tronquée après '10'")
                rank_raw = "10"
                suit_raw = blob[j+2]
                j += 3
            else:
                if j + 1 >= len(blob):
                    raise CardParseError("Chaîne invalide (rank sans suit)")
                rank_raw = blob[j]
                suit_raw = blob[j+1]
                j += 2
            r = _norm_rank(rank_raw)
            s = _norm_suit(suit_raw)
            tokens.append(r + s.lower())
    return tokens


def parse_combo(combo: str) -> Tuple[int, int]:
    """Parse une main de 2 cartes (ex: 'AhKh' ou 'Ah Kh' ou 'AH-KH').

    Retourne (c1, c2) en entiers distincts. Lève CardParseError en cas de doublons.
    """
    toks = _tokenize_cards(combo)
    if len(toks) != 2:
        raise CardParseError(f"Une main doit contenir exactement 2 cartes (reçu: {len(toks)}): {combo!r}")
    c1, c2 = (parse_card(toks[0]), parse_card(toks[1]))
    if c1 == c2:
        raise CardParseError("Doublon de carte dans la main (même carte utilisée deux fois)")
    return c1, c2


def parse_board(board: str | None) -> List[int]:
    """Parse un board partiel/total.

    Accepte 0, 3, 4 ou 5 cartes. Lève CardParseError si autre cardinalité.
    """
    if not board:
        return []
    toks = _tokenize_cards(board)
    if len(toks) not in (3, 4, 5):
        raise CardParseError(
            f"Le board doit avoir 3, 4 ou 5 cartes (reçu: {len(toks)}): {board!r}"
        )
    cards = [parse_card(t) for t in toks]
    ensure_no_duplicates(cards)
    return cards


# =========================
# Deck et validations
# =========================

def deck52() -> List[int]:
    """Retourne la liste des 52 cartes (0..51)."""
    return list(range(52))


def ensure_no_duplicates(cards: Sequence[int]) -> None:
    """Lève si des doublons sont détectés dans une séquence de cartes."""
    s = set(cards)
    if len(s) != len(cards):
        # Identifier les doublons pour un message explicite
        seen = set()
        dups = []
        for c in cards:
            if c in seen and c not in dups:
                dups.append(c)
            seen.add(c)
        if dups:
            pretty = ", ".join(card_to_str(c) for c in dups)
            raise CardParseError(f"Doublons détectés: {pretty}")
        raise CardParseError("Doublons détectés dans les cartes fournies")


def deck_without(known: Iterable[int]) -> List[int]:
    """Deck des 52 cartes en retirant celles de `known`.

    Lève si `known` contient des doublons ou des indices hors borne.
    """
    known_list = list(known)
    # validations
    for c in known_list:
        if not (0 <= c <= 51):
            raise CardParseError(f"Index carte hors bornes dans known: {c}")
    ensure_no_duplicates(known_list)

    all_cards = set(range(52))
    remaining = sorted(all_cards.difference(known_list))
    # Sanity: taille cohérente
    if len(remaining) != 52 - len(known_list):
        raise CardParseError("Incohérence de deck après retrait des cartes connues")
    return remaining
