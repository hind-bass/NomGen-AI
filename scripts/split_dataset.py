"""
split_dataset.py — Jour 1
Divise dataset_fr.txt et dataset_ar.txt en sous-fichiers par catégorie + type.

Structure de sortie :
  data/
  ├── fr/marque/tech.txt
  ├── fr/marque/food.txt
  ├── fr/marque/luxe.txt
  ├── fr/marque/general.txt
  ├── fr/societe/tech.txt
  ├── fr/societe/food.txt
  ├── fr/societe/luxe.txt
  ├── fr/societe/general.txt
  ├── ar/marque/tech.txt
  ├── ar/marque/food.txt
  ├── ar/marque/luxe.txt
  └── ar/marque/general.txt

Exécution : python scripts/split_dataset.py (depuis la racine du projet)
"""
import os
import re

# ─── Chemins ─────────────────────────────────────────────────────────────────
ROOT_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(ROOT_DIR, "data")
FR_SRC    = os.path.join(DATA_DIR, "dataset_fr.txt")
AR_SRC    = os.path.join(DATA_DIR, "dataset_ar.txt")


# ─── Règles de classification FR ─────────────────────────────────────────────
# Mots-clés → catégorie
CATEGORIE_RULES_FR = {
    "tech": [
        "tech", "digit", "info", "bit", "byte", "data", "cloud", "net",
        "soft", "web", "code", "cyber", "pixel", "algo", "ia", "app",
        "smart", "innov", "logic", "system", "nexo", "nexia", "coder",
    ],
    "food": [
        "food", "aliment", "cuisiн", "gastro", "gourm", "boulang",
        "pastiss", "traiteur", "saveur", "goût", "manger", "bouffe",
        "restaurant", "bistr", "snack", "biscuit", "chocolat", "patiss",
        "bonapp", "delici", "gustat", "gastr",
    ],
    "luxe": [
        "luxe", "luxu", "premium", "prestig", "coutur", "bijou", "joaille",
        "parfum", "beauté", "elegan", "mode", "fashion", "luxori",
        "haute", "raffi", "exclus", "gold", "platine", "diamant",
    ],
}

# Mots-clés → type (marque vs société)
SOCIETE_KEYWORDS = [
    "conseil", "expert", "pro", "services", "solutions", "consulting",
    "groupe", "holding", "associé", "cabinet", "agence", "studio",
    "entreprise", "société", "sarl", "sas", "sa ", "industri",
    "batiment", "bâtiment", "construction", "btp", "charpent",
    "plomberie", "electricit", "chauffage", "climatisation", "isolation",
    "renovation", "toiture", "menuiseri", "carrelage", "peinture",
    "nettoyage", "jardinage", "paysage", "déménagement", "transport",
    "distribution", "logistique", "import", "export", "négoce",
]


def classify_fr(name: str) -> tuple[str, str]:
    """
    Retourne (categorie, type_nom) pour un nom français.
    categorie : "tech" | "food" | "luxe" | "general"
    type_nom  : "marque" | "societe"
    """
    n = name.lower()

    # Catégorie
    categorie = "general"
    for cat, keywords in CATEGORIE_RULES_FR.items():
        if any(kw in n for kw in keywords):
            categorie = cat
            break

    # Type
    type_nom = "societe" if any(kw in n for kw in SOCIETE_KEYWORDS) else "marque"

    return categorie, type_nom


# ─── Règles de classification AR ─────────────────────────────────────────────
CATEGORIE_RULES_AR = {
    "tech": [
        "تقن", "ذكاء", "برمج", "إنترن", "كلاود", "ديجيت", "سوفت",
        "نت", "ويب", "سمارت", "روبوت", "ديتا", "ستارتب",
    ],
    "food": [
        "غذاء", "أكل", "طعام", "مطبخ", "طازج", "لذيذ", "حلو", "خبز",
        "دانون", "نستل", "مراعي", "شهية", "طرية", "فواكه", "خضروات",
    ],
    "luxe": [
        "فاخر", "راقي", "بريميوم", "لوكس", "مميز", "جوهر", "بلور",
        "ياقوت", "لؤلؤ", "ذهب", "فضة", "ماس",
    ],
}


def classify_ar(name: str) -> tuple[str, str]:
    """Retourne (categorie, type_nom) pour un nom arabe."""
    categorie = "general"
    for cat, keywords in CATEGORIE_RULES_AR.items():
        if any(kw in name for kw in keywords):
            categorie = cat
            break
    # Pour l'arabe, on classe tout en "marque" par défaut
    # (les noms de société arabes sont plus difficiles à distinguer sans contexte)
    return categorie, "marque"


# ─── Lecture des fichiers source ──────────────────────────────────────────────
def read_names(filepath: str) -> list[str]:
    """Lit un fichier de noms et retourne une liste dédoublonnée."""
    if not os.path.exists(filepath):
        print(f"⚠️  Fichier introuvable : {filepath}")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        names = [line.strip() for line in f if line.strip()]
    # Dédoublonnage
    return list(dict.fromkeys(names))


# ─── Écriture des fichiers de sortie ─────────────────────────────────────────
def write_names(names: list[str], filepath: str):
    """Écrit une liste de noms dans un fichier (crée les dossiers si besoin)."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        for name in sorted(set(names)):
            f.write(name + "\n")


# ─── Traitement principal ─────────────────────────────────────────────────────
def split_french():
    """Split dataset_fr.txt en fichiers par catégorie + type."""
    names = read_names(FR_SRC)
    print(f"\n📂 Traitement FR : {len(names)} noms")

    buckets: dict[str, list[str]] = {}

    for name in names:
        cat, typ = classify_fr(name)
        key = f"fr/{typ}/{cat}"
        buckets.setdefault(key, []).append(name)

    for key, bucket_names in buckets.items():
        out_path = os.path.join(DATA_DIR, key + ".txt")
        write_names(bucket_names, out_path)
        print(f"  ✓ {key}.txt — {len(bucket_names)} noms")

    return buckets


def split_arabic():
    """Split dataset_ar.txt en fichiers par catégorie."""
    names = read_names(AR_SRC)
    print(f"\n📂 Traitement AR : {len(names)} noms")

    buckets: dict[str, list[str]] = {}

    for name in names:
        cat, typ = classify_ar(name)
        key = f"ar/{typ}/{cat}"
        buckets.setdefault(key, []).append(name)

    for key, bucket_names in buckets.items():
        out_path = os.path.join(DATA_DIR, key + ".txt")
        write_names(bucket_names, out_path)
        print(f"  ✓ {key}.txt — {len(bucket_names)} noms")

    return buckets


def print_summary(fr_buckets: dict, ar_buckets: dict):
    """Affiche un résumé des fichiers créés."""
    total_files = len(fr_buckets) + len(ar_buckets)
    total_names = sum(len(v) for v in fr_buckets.values()) + \
                  sum(len(v) for v in ar_buckets.values())
    print(f"\n{'─'*50}")
    print(f"✅ Split terminé : {total_files} fichiers, {total_names} noms distribués")
    print(f"{'─'*50}")
    print("\nStructure générée dans data/ :")
    for key in sorted(fr_buckets.keys()):
        print(f"  data/{key}.txt ({len(fr_buckets[key])} noms)")
    for key in sorted(ar_buckets.keys()):
        print(f"  data/{key}.txt ({len(ar_buckets[key])} noms)")


if __name__ == "__main__":
    print("🚀 split_dataset.py — NomGen AI Jour 1")
    fr_buckets = split_french()
    ar_buckets = split_arabic()
    print_summary(fr_buckets, ar_buckets)
