"""
check_dataset.py — Jour 1
Outil de qualité pour tous les fichiers de données.
- Détecte les doublons
- Vérifie les longueurs minimales/maximales
- Génère un rapport de stats
- Nettoie et réécrit les fichiers proprement

Exécution : python check_dataset.py
"""
import os
import glob
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


def check_file(filepath: str) -> dict:
    """
    Analyse un fichier de noms et retourne un rapport.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw_lines = [l.strip() for l in f if l.strip()]

    total = len(raw_lines)
    unique = list(dict.fromkeys(raw_lines))  # Préserve l'ordre + dédoublonne
    duplicates = total - len(unique)

    # Vérification des longueurs
    too_short = [n for n in unique if len(n) < 2]
    too_long  = [n for n in unique if len(n) > 30]
    valid     = [n for n in unique if 2 <= len(n) <= 30]

    lengths = [len(n) for n in unique]
    avg_len = sum(lengths) / len(lengths) if lengths else 0

    return {
        "filepath": filepath,
        "total": total,
        "unique": len(unique),
        "duplicates": duplicates,
        "too_short": len(too_short),
        "too_long": len(too_long),
        "valid": len(valid),
        "avg_len": round(avg_len, 1),
        "valid_names": valid,
    }


def clean_file(filepath: str, report: dict):
    """Réécrit le fichier avec seulement les noms valides et sans doublons."""
    with open(filepath, "w", encoding="utf-8") as f:
        for name in sorted(report["valid_names"]):
            f.write(name + "\n")


def run():
    """Lance l'analyse sur tous les fichiers .txt du dossier data/."""
    # Chercher tous les fichiers .txt récursivement
    pattern = os.path.join(DATA_DIR, "**", "*.txt")
    files   = glob.glob(pattern, recursive=True)

    if not files:
        print(f"⚠️  Aucun fichier .txt trouvé dans {DATA_DIR}")
        print("   Lancez d'abord split_dataset.py !")
        return

    print(f"🔍 Analyse de {len(files)} fichiers dans data/\n")
    print(f"{'Fichier':<45} {'Total':>6} {'Uniques':>8} {'Doublons':>9} {'Valides':>8} {'MoyLen':>7}")
    print("─" * 85)

    total_issues = 0
    reports = []

    for filepath in sorted(files):
        report = check_file(filepath)
        reports.append(report)

        rel_path = os.path.relpath(filepath, DATA_DIR)
        issues = report["duplicates"] + report["too_short"] + report["too_long"]
        total_issues += issues

        flag = "⚠️ " if issues > 0 else "✅"
        print(
            f"{flag} {rel_path:<43} "
            f"{report['total']:>6} "
            f"{report['unique']:>8} "
            f"{report['duplicates']:>9} "
            f"{report['valid']:>8} "
            f"{report['avg_len']:>7}"
        )

    print("─" * 85)
    print(f"\n📊 Résumé : {len(files)} fichiers | {total_issues} problèmes détectés")

    if total_issues > 0:
        print("\n🔧 Nettoyage automatique en cours...")
        cleaned = 0
        for report in reports:
            issues = report["duplicates"] + report["too_short"] + report["too_long"]
            if issues > 0:
                clean_file(report["filepath"], report)
                rel = os.path.relpath(report["filepath"], DATA_DIR)
                print(f"  ✓ Nettoyé : {rel} ({report['valid']} noms valides conservés)")
                cleaned += 1
        print(f"\n✅ {cleaned} fichier(s) nettoyé(s) et réécrits proprement.")
    else:
        print("✅ Tous les fichiers sont propres, aucun nettoyage nécessaire.")

    # Rapport croisé — doublons entre fichiers
    print("\n🔎 Recherche de doublons ENTRE fichiers...")
    name_to_files = defaultdict(list)
    for report in reports:
        rel = os.path.relpath(report["filepath"], DATA_DIR)
        for name in report["valid_names"]:
            name_to_files[name.lower()].append(rel)

    cross_dupes = {
        name: paths
        for name, paths in name_to_files.items()
        if len(paths) > 1
    }

    if cross_dupes:
        print(f"  ⚠️  {len(cross_dupes)} nom(s) présent(s) dans plusieurs fichiers :")
        for name, paths in list(cross_dupes.items())[:10]:  # Affiche max 10
            print(f"     '{name}' → {', '.join(paths)}")
    else:
        print("  ✅ Aucun doublon inter-fichiers détecté.")


if __name__ == "__main__":
    run()
