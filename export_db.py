#!/usr/bin/env python3
"""
Export donnees BD en CSV.
"""

import sqlite3
import csv
from pathlib import Path

DB_PATH = Path(__file__).parent / "backend" / "nomgen.db"


def export_table(table_name: str):
    """Export une table en CSV."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Lire la table
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    # En-tetes
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]

    # Ecrire CSV
    output_file = Path(__file__).parent / f"export_{table_name}.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)

    print(f"[OK] {table_name}: {len(rows)} rows -> {output_file}")
    conn.close()


if __name__ == "__main__":
    print("Exportation des donnees...\n")
    for table in ["user", "suggestion", "favorite", "history", "reservation"]:
        try:
            export_table(table)
        except Exception as e:
            print(f"[ERREUR] {table}: {e}")
    print("\nFait!")
