"""Scoring de plausibilité heuristique pour les noms générés."""
import re


def score_fr(name: str) -> float:
    if not name or len(name) < 2:
        return 0.0
    score  = 50
    vowels = set("aeiouy")
    L      = len(name)

    # Longueur optimale
    if 4 <= L <= 8:    score += 20
    elif 3 <= L <= 10: score += 10
    elif L > 12:       score -= 10

    # Terminaisons typiques des marques FR
    nice = ["eau","ine","or","el","on","eur","ais","ie","ia","al","ux","elle","ance"]
    if any(name.endswith(e) for e in nice): score += 15

    # Début par consonne forte
    if name[0] in "bcdfghjklmnprstv": score += 8

    # Euphonie : alternance consonnes/voyelles
    alt = sum(1 for i in range(L - 1)
              if (name[i] in vowels) != (name[i+1] in vowels))
    score += min(int(alt / max(L - 1, 1) * 15), 15)

    # Pas trop de consonnes consécutives
    cc = [len(m.group()) for m in re.finditer(r"[^aeiouy]+", name)]
    if cc and max(cc) > 3: score -= 15

    return float(max(0, min(100, score)))


def score_ar(name: str) -> float:
    if not name or len(name) < 2:
        return 0.0
    score        = 50
    vowel_tokens = {"\u0627", "\u0648", "\u064a"}
    L            = len(name)

    if 3 <= L <= 6:  score += 25
    elif L <= 8:     score += 12
    else:            score -= 5

    alt = sum(1 for i in range(L - 1)
              if (name[i] in vowel_tokens) != (name[i+1] in vowel_tokens))
    score += min(int(alt / max(L - 1, 1) * 20), 20)

    if name[0] not in {"\u0621", "\u0623", "\u0625"}: score += 10
    if name.endswith("\u0629"): score += 10

    return float(max(0, min(100, score)))
