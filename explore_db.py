#!/usr/bin/env python3
"""
Script pour explorer et afficher les donnees SQLite.
Montre tous les utilisateurs, suggestions, etc.
"""

import sqlite3
from pathlib import Path
from tabulate import tabulate  # pip install tabulate

DB_PATH = Path(__file__).parent / "backend" / "nomgen.db"


def query_db(query: str):
    """Execute une requete et retourne les resultats."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


def print_users():
    """Affiche tous les utilisateurs."""
    print("\n" + "="*80)
    print("UTILISATEURS (Users)")
    print("="*80)

    users = query_db("SELECT id, email, role, is_active, created_at FROM user")
    if users:
        data = [
            [u["id"], u["email"], u["role"], "Actif" if u["is_active"] else "Inactif", u["created_at"][:10]]
            for u in users
        ]
        print(tabulate(data, headers=["ID", "Email", "Role", "Statut", "Date"], tablefmt="grid"))
    else:
        print("Aucun utilisateur")


def print_suggestions():
    """Affiche toutes les suggestions."""
    print("\n" + "="*80)
    print("SUGGESTIONS")
    print("="*80)

    suggestions = query_db("""
        SELECT id, nom, langue, secteur, type_nom, status, user_id, submitted_at
        FROM suggestion
        ORDER BY submitted_at DESC
    """)

    if suggestions:
        data = [
            [
                s["id"],
                s["nom"],
                s["langue"],
                s["secteur"],
                s["type_nom"],
                s["status"].upper(),
                s["user_id"],
                s["submitted_at"][:10]
            ]
            for s in suggestions
        ]
        print(tabulate(
            data,
            headers=["ID", "Nom", "Langue", "Secteur", "Type", "Statut", "User", "Date"],
            tablefmt="grid"
        ))
    else:
        print("Aucune suggestion")


def print_suggestions_stats():
    """Statistiques des suggestions."""
    print("\n" + "="*80)
    print("STATISTIQUES SUGGESTIONS")
    print("="*80)

    stats = query_db("""
        SELECT
            status,
            COUNT(*) as count,
            COUNT(DISTINCT user_id) as users
        FROM suggestion
        GROUP BY status
    """)

    if stats:
        data = [[s["status"].upper(), s["count"], s["users"]] for s in stats]
        print(tabulate(data, headers=["Statut", "Total", "Utilisateurs"], tablefmt="grid"))

    # Langues
    print("\nPar Langue:")
    langs = query_db("""
        SELECT langue, COUNT(*) as count, status
        FROM suggestion
        GROUP BY langue, status
    """)

    if langs:
        data = [[l["langue"], l["count"], l["status"].upper()] for l in langs]
        print(tabulate(data, headers=["Langue", "Count", "Statut"], tablefmt="grid"))


def print_favorites():
    """Affiche les favoris."""
    print("\n" + "="*80)
    print("FAVORIS")
    print("="*80)

    favs = query_db("""
        SELECT id, user_id, nom, score, langue, secteur, created_at
        FROM favorite
        ORDER BY score DESC
    """)

    if favs:
        data = [
            [f["id"], f["user_id"], f["nom"], f"{f['score']:.2f}", f["langue"], f["secteur"], f["created_at"][:10]]
            for f in favs
        ]
        print(tabulate(data, headers=["ID", "User", "Nom", "Score", "Langue", "Secteur", "Date"], tablefmt="grid"))
    else:
        print("Aucun favori")


def print_dataset_files():
    """Affiche les fichiers dataset generes."""
    print("\n" + "="*80)
    print("FICHIERS DATASET GENERES")
    print("="*80)

    data_dir = Path(__file__).parent.parent.parent / "data"
    if data_dir.exists():
        for txt_file in sorted(data_dir.rglob("*.txt")):
            rel_path = txt_file.relative_to(data_dir)
            with open(txt_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            print(f"\n{rel_path}")
            print(f"  Items: {len(lines)}")
            if lines:
                print(f"  Premiers: {', '.join([l.strip() for l in lines[:3]])}")
    else:
        print("Dossier /data n'existe pas encore")


def print_db_info():
    """Affiche les infos de la BD."""
    print("\n" + "="*80)
    print("INFORMATIONS BASE DE DONNEES")
    print("="*80)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables: {len(tables)}")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  - {table[0]}: {count} rows")

    conn.close()
    print(f"\nFichier: {DB_PATH}")
    print(f"Taille: {DB_PATH.stat().st_size / 1024:.1f} KB")


def main():
    """Affiche toutes les donnees."""
    print("\n" + "="*80)
    print("===  EXPLORATION BASE DE DONNEES NOMGEN  ===")
    print("="*80)

    try:
        print_db_info()
        print_users()
        print_suggestions()
        print_suggestions_stats()
        print_favorites()
        print_dataset_files()

        print("\n" + "="*80)
        print("FIN DE L'EXPLORATION")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\nErreur: {e}")
        print("Assurez-vous que le serveur backend est en cours d'execution")


if __name__ == "__main__":
    main()
