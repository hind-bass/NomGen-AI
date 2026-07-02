"""Restore or merge nomgen.db from git history after accidental deletion."""
from __future__ import annotations

import argparse
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
CURRENT_DB = BACKEND / "nomgen.db"
BACKUP_DB = BACKEND / "nomgen.db.pre_merge_backup"

TABLES_TO_MERGE = ("history", "favorite", "favoris", "generations", "feedback", "suggestion", "reservation")


def extract_db_from_commit(commit: str, dest: Path) -> None:
    blob = subprocess.check_output(
        ["git", "rev-parse", f"{commit}:backend/nomgen.db"],
        cwd=ROOT,
        text=True,
    ).strip()
    raw = subprocess.check_output(["git", "cat-file", "blob", blob], cwd=ROOT)
    dest.write_bytes(raw)


def count_rows(db_path: Path) -> dict[str, int]:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    counts = {}
    for table in tables:
        counts[table] = cur.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
    conn.close()
    return counts


def merge_missing_rows(target: Path, source: Path) -> dict[str, int]:
    """Copy rows from source into target when their primary key is absent."""
    merged: dict[str, int] = {}
    conn = sqlite3.connect(target)
    conn.execute(f"ATTACH DATABASE ? AS src", (str(source),))
    cur = conn.cursor()
    for table in TABLES_TO_MERGE:
        cur.execute(f'SELECT name FROM src.sqlite_master WHERE type="table" AND name=?', (table,))
        if not cur.fetchone():
            continue
        before = cur.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        cur.execute(
            f'INSERT OR IGNORE INTO "{table}" SELECT * FROM src."{table}"'
        )
        after = cur.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        merged[table] = after - before
    conn.commit()
    conn.execute("DETACH DATABASE src")
    conn.close()
    return merged


def restore(commit: str, mode: str) -> None:
    print(f"Extraction de backend/nomgen.db depuis {commit}...")
    extract_db_from_commit(commit, BACKUP_DB)

    if not CURRENT_DB.exists():
        shutil.copy2(BACKUP_DB, CURRENT_DB)
        print(f"Base restaurée -> {CURRENT_DB}")
        return

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safety_copy = BACKEND / f"nomgen.db.before_restore_{stamp}"
    shutil.copy2(CURRENT_DB, safety_copy)
    print(f"Sauvegarde de la base actuelle -> {safety_copy.name}")

    if mode == "replace":
        shutil.copy2(BACKUP_DB, CURRENT_DB)
        print("Mode replace: ancienne base Git réinstallée.")
    else:
        merged = merge_missing_rows(CURRENT_DB, BACKUP_DB)
        print("Mode merge: lignes récupérées:")
        for table, added in merged.items():
            if added:
                print(f"  {table}: +{added}")

    before = count_rows(safety_copy)
    after = count_rows(CURRENT_DB)
    print("\nAvant -> Après")
    for table in sorted(set(before) | set(after)):
        print(f"  {table}: {before.get(table, 0)} -> {after.get(table, 0)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Restaurer nomgen.db depuis git.")
    parser.add_argument("--commit", default="98e1292", help="Commit git contenant nomgen.db")
    parser.add_argument(
        "--mode",
        choices=("merge", "replace"),
        default="merge",
        help="merge = conserver le récent + récupérer l'ancien ; replace = remplacer entièrement",
    )
    parser.add_argument("--apply", action="store_true", help="Appliquer la restauration")
    args = parser.parse_args()

    if not args.apply:
        extract_db_from_commit(args.commit, BACKUP_DB)
        print("Inspection seulement (--apply absent).")
        print("Backup git:", count_rows(BACKUP_DB))
        if CURRENT_DB.exists():
            print("Base actuelle:", count_rows(CURRENT_DB))
        print("\nRelancez avec: python backend/scripts/restore_db_from_git.py --apply")
        return

    try:
        restore(args.commit, args.mode)
    except PermissionError:
        print(
            "\nErreur: nomgen.db est verrouillée (backend en cours d'exécution).\n"
            "Arrêtez uvicorn, puis relancez:\n"
            "  python backend/scripts/restore_db_from_git.py --apply"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
