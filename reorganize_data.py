"""
reorganize_data.py — Jour 2
Nettoie et réorganise le dossier data/.

Actions :
  1. Fusionne les fichiers plats redondants dans la structure canonique
  2. Supprime les doublons INTER-fichiers
  3. Supprime les anciens fichiers plats
  4. Affiche un rapport final

Exécution : python reorganize_data.py  (depuis la racine du projet)
"""
import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ─── Fichiers à FUSIONNER puis SUPPRIMER ─────────────────────────────────────
# Format : (source_à_supprimer, destination_canonique)
MERGES = [
    # FR
    ("fr/marque_luxe.txt",       "fr/marque/luxe.txt"),
    ("fr/marque_food.txt",       "fr/marque/food.txt"),
    ("fr/societe_tech.txt",      "fr/societe/tech.txt"),
    ("fr/societe_services.txt",  "fr/societe/general.txt"),
    ("fr/societe_industrie.txt", "fr/societe/general.txt"),
    ("fr/societe_general.txt",   "fr/societe/general.txt"),
    # AR
    ("ar/marque_tech.txt",       "ar/marque/tech.txt"),
    ("ar/marque_food.txt",       "ar/marque/food.txt"),
    ("ar/marque_luxe.txt",       "ar/marque/luxe.txt"),
    ("ar/societe_general.txt",   "ar/societe/general.txt"),
    ("ar/societe_services.txt",  "ar/societe/general.txt"),
    ("ar/societe_industrie.txt", "ar/societe/general.txt"),
]


def read_names(path: str) -> list[str]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]


def write_names(names: list[str], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    unique = sorted(set(n.lower() for n in names if len(n) >= 2))
    with open(path, "w", encoding="utf-8") as f:
        for n in unique:
            f.write(n + "\n")
    return len(unique)


def run():
    print("🔧 Réorganisation du dossier data/\n")
    merged_count = 0
    deleted = []

    for src_rel, dst_rel in MERGES:
        src = os.path.join(DATA_DIR, src_rel)
        dst = os.path.join(DATA_DIR, dst_rel)

        if not os.path.exists(src):
            print(f"  ⏭️  Ignoré (absent) : {src_rel}")
            continue

        # Lire les deux fichiers
        src_names = read_names(src)
        dst_names = read_names(dst)

        # Fusionner
        merged = list(set(dst_names + src_names))
        count = write_names(merged, dst)
        print(f"  ✅ Fusionné : {src_rel} → {dst_rel} ({count} noms uniques)")

        # Supprimer la source
        os.remove(src)
        deleted.append(src_rel)
        merged_count += len(src_names)

    print(f"\n📊 {len(deleted)} fichiers supprimés, {merged_count} noms fusionnés")
    print("\n✅ Structure canonique finale :")
    for root, dirs, files in os.walk(DATA_DIR):
        dirs.sort()
        level = root.replace(DATA_DIR, "").count(os.sep)
        indent = "  " * level
        folder = os.path.basename(root)
        if level > 0:
            print(f"{indent}📁 {folder}/")
        for f in sorted(files):
            if f.endswith(".txt"):
                path = os.path.join(root, f)
                count = len(read_names(path))
                sub = "  " * (level + 1)
                print(f"{sub}📄 {f}  ({count} noms)")


if __name__ == "__main__":
    run()