"""
filter_test.py — Test de la logique de filtrage sur un échantillon réel.
Objectif: valider les règles avant de les mettre dans le notebook.
"""
import re
from pathlib import Path
from collections import Counter

def load_names(path):
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

def normalize_arabic(text):
    text = text.strip()

    # enlever les voyelles
    text = re.sub(r'[\u064B-\u065F]', '', text)

    # unifier les formes
    text = text.replace('أ', 'ا')
    text = text.replace('إ', 'ا')
    text = text.replace('آ', 'ا')
    text = text.replace('ة', 'ه')
    text = text.replace('ى', 'ي')

    return text

def is_composed(name: str) -> bool:
    """Un nom est 'composé' s'il contient un espace ou une apostrophe multi-mot,
    ou s'il ressemble à 'marque + suffixe pays' (ex: 'chanel', 'dior france')."""
    return " " in name or "'" in name

def is_brand_plus_country_suffix(name: str) -> bool:
    """Détecte 'xxx france', 'xxx paris' etc."""
    suffixes = [" france", " paris", " usa"]
    return any(name.lower().endswith(s) for s in suffixes)

KNOWN_REAL_BRANDS = {
    "chanel", "dior", "hermes", "guerlain", "lancome", "balmain", "carven",
    "caudalie", "fauchon", "givenchy", "jacquemus", "rochas", "repossi",
    "messika", "mauboussin", "rabanne", "gaultier", "goutal", "diptyque",
    "dyptique", "garlande",
}

def is_known_real_brand(name: str) -> bool:
    base = name.lower().split(" france")[0].split(" paris")[0].strip()
    return base in KNOWN_REAL_BRANDS

def dedupe_radical_families(names, prefix_len=3, max_per_family=4):
    from collections import defaultdict

    families = defaultdict(list)

    for n in names:
        key = normalize_arabic(n)[:prefix_len]
        families[key].append(n)

    kept = []

    for members in families.values():
        members_sorted = sorted(members, key=len)
        kept.extend(members_sorted[:max_per_family])

    return kept

def is_arabic_word(name):
    return bool(re.fullmatch(r'[\u0600-\u06FF]+', name))


def detect_repetitive_suffix_patterns(names, min_repeat=5):
    """Détecte les suffixes répétés un trop grand nombre de fois
    (signe de génération combinatoire 'mot+suffixe' artificielle).
    Renvoie le set des suffixes à risque."""
    suffix_counter = Counter()
    for n in names:
        n_clean = n.lower().replace(" ", "")
        if len(n_clean) > 4:
            suffix_counter[n_clean[-4:]] += 1
    risky = {suf for suf, count in suffix_counter.items() if count >= min_repeat}
    return risky

ROOT = Path(__file__).resolve().parent.parent

for file in (ROOT / "data" / "ar").rglob("*.txt"):
    names = load_names(file)
    print(file, len(names))
    names = [n for n in names if is_arabic_word(n)]
    names = [n for n in names if not is_composed(n)]
    names = [n for n in names
             if not is_brand_plus_country_suffix(n)
             and not is_known_real_brand(n)]

    names = dedupe_radical_families(names)

    # doublons exacts
    seen = set()
    unique_names = []

    for name in names:
      norm = normalize_arabic(name)
 
      if norm not in seen:
        seen.add(norm)
        unique_names.append(name)

    names = unique_names

    with open(file, "w", encoding="utf-8") as f:
        f.write("\n".join(names))

    print(f"{file}: {len(names)} noms")

# Filtre 1: noms composés (espace ou apostrophe)
composed = [n for n in names if is_composed(n)]
single = [n for n in names if not is_composed(n)]
print(f"Composés (rejetés): {len(composed)}")
print(f"Un seul mot (gardés pour l'instant): {len(single)}")
print("Exemples composés rejetés:", composed[:8])

# Filtre 2: marques réelles connues avec suffixe pays
real_brand_suffix = [n for n in single if is_brand_plus_country_suffix(n)]
print(f"\nMarques+suffixe pays (rejetés): {len(real_brand_suffix)}")
print("Exemples:", real_brand_suffix[:8])

clean = [n for n in single if not is_brand_plus_country_suffix(n) and not is_known_real_brand(n)]
print(f"\nRestant après filtre 1+2 (composés + marques réelles): {len(clean)}")

# Filtre 3: dédupliquer les familles de radicaux sur-représentées
deduped = dedupe_radical_families(clean, prefix_len=3, max_per_family=4)
print(f"Restant après dédoublonnage des familles de radicaux: {len(deduped)}")
print("Exemples finaux:", sorted(deduped)[:20])