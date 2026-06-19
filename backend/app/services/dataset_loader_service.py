"""
Chargement des datasets statiques (data/fr, data/ar).

Utilisé pour le few-shot prompting des LLM locaux (Mode B)
et comme base de référence pour le fine-tuning.
"""
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

# Mapping secteur API → dossier dataset
SECTEUR_MAP = {
    "general": "general",
    "tous": "general",
    "tech": "tech",
    "luxe": "luxe",
    "food": "food",
    "minimal": "general",
    "futuriste": "tech",
    "corporate": "general",
}


def normalize_secteur(secteur: str) -> str:
    """Normalise un secteur vers la clé de fichier dataset."""
    key = secteur.lower().strip()
    return SECTEUR_MAP.get(key, "general")


def normalize_type(type_nom: str) -> str:
    """Normalise le type vers 'marque' ou 'societe'."""
    t = type_nom.lower().strip()
    if t in ("societe", "entreprise", "company"):
        return "societe"
    return "marque"


def dataset_file_path(langue: str, secteur: str, type_nom: str) -> Path:
    """Retourne le chemin du fichier .txt correspondant."""
    lang = langue.lower().strip()[:2]
    if lang not in ("fr", "ar"):
        lang = "fr"
    cat = normalize_secteur(secteur)
    typ = normalize_type(type_nom)
    return DATA_DIR / lang / typ / f"{cat}.txt"


def load_names_from_file(path: Path, limit: int = 20) -> list[str]:
    """Charge des noms depuis un fichier dataset (échantillon aléatoire)."""
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        names = [line.strip() for line in f if line.strip() and len(line.strip()) >= 2]
    if not names:
        return []
    if len(names) <= limit:
        return names
    return random.sample(names, limit)


def load_few_shot_examples(
    langue: str,
    secteur: str,
    type_nom: str,
    limit: int = 8,
) -> list[str]:
    """
    Charge des exemples few-shot depuis le dataset statique.
    Fallback vers general.txt si le fichier spécialisé est absent.
    """
    primary = dataset_file_path(langue, secteur, type_nom)
    names = load_names_from_file(primary, limit=limit)

    if len(names) < limit // 2:
        fallback = dataset_file_path(langue, "general", type_nom)
        if fallback != primary:
            extra = load_names_from_file(fallback, limit=limit - len(names))
            names = list(dict.fromkeys(names + extra))

    return names[:limit]


def append_name_to_dataset(
    langue: str,
    secteur: str,
    type_nom: str,
    nom: str,
) -> bool:
    """
    Ajoute un nom validé au fichier dataset s'il n'existe pas déjà.
    Retourne True si ajouté, False si déjà présent ou nom invalide.
    """
    nom_clean = nom.strip().lower()
    if len(nom_clean) < 2:
        return False

    path = dataset_file_path(langue, secteur, type_nom)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing: set[str] = set()
    if path.exists():
        with open(path, encoding="utf-8") as f:
            existing = {line.strip().lower() for line in f if line.strip()}

    if nom_clean in existing:
        return False

    with open(path, "a", encoding="utf-8") as f:
        f.write(nom_clean + "\n")
    return True


def count_dataset_names() -> dict:
    """Compte les noms par langue/secteur dans les fichiers statiques."""
    stats: dict = {"fr": 0, "ar": 0, "total": 0, "files": 0}
    for lang in ("fr", "ar"):
        lang_dir = DATA_DIR / lang
        if not lang_dir.exists():
            continue
        for txt in lang_dir.rglob("*.txt"):
            with open(txt, encoding="utf-8") as f:
                count = sum(1 for line in f if line.strip())
            stats[lang] += count
            stats["total"] += count
            stats["files"] += 1
    return stats
