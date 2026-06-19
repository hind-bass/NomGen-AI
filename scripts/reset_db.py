#!/usr/bin/env python3
"""
Reinitialiser la base de donnees.
WARNING: Supprime TOUTES les donnees!
"""

import sqlite3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "backend" / "nomgen.db"


def reset_database():
    """Supprime toutes les donnees et cree un admin par defaut."""
    if not DB_PATH.exists():
        print("Base de donnees non trouvee")
        return

    response = input("Confirmer la reinitialisation? (yes/no): ")
    if response.lower() != "yes":
        print("Annule")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Supprimer toutes les donnees
        cursor.execute("DELETE FROM feedback")
        cursor.execute("DELETE FROM favori")
        cursor.execute("DELETE FROM generation")
        cursor.execute("DELETE FROM suggestion")
        cursor.execute("DELETE FROM favorite")
        cursor.execute("DELETE FROM history")
        cursor.execute("DELETE FROM reservation")
        cursor.execute("DELETE FROM user")

        conn.commit()
        print("\n[OK] Base de donnees reinitalisee")
        print("Redemarrez le serveur pour creer l'admin par defaut")

    except Exception as e:
        print(f"[ERREUR] {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    print("="*60)
    print("REINITIALISATION BASE DE DONNEES")
    print("="*60)
    reset_database()
