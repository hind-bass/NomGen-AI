#!/usr/bin/env python3
"""
Script de création / initialisation de la base SQLite.

Usage (depuis le dossier backend/) :
    python -m app.database.init_db
    python -m app.database.init_db --seed   # insère des données d'exemple
"""
import argparse
from datetime import datetime, timedelta

from sqlmodel import Session

from app.database.connection import create_db_and_tables, engine
from app.models.feedback_models import Favori, Feedback, Generation


def seed_sample_data(session: Session) -> None:
    """Insère des générations, votes et favoris d'exemple pour les tests Postman."""
    base_date = datetime.utcnow()

    generations = [
        Generation(
            prompt="marque de luxe pour parfums",
            langue="fr",
            categorie="LUXE",
            type_nom="marque",
            nom_genere="Veloria",
            score=82.0,
            mode="B",
            created_at=base_date - timedelta(hours=2),
        ),
        Generation(
            prompt="startup tech intelligence artificielle",
            langue="fr",
            categorie="TECH",
            type_nom="societe",
            nom_genere="NeuraLink",
            score=75.5,
            mode="B",
            created_at=base_date - timedelta(hours=1),
        ),
        Generation(
            prompt="restaurant bio méditerranéen",
            langue="fr",
            categorie="FOOD",
            type_nom="marque",
            nom_genere="Solvita",
            score=68.0,
            mode="A",
            created_at=base_date - timedelta(minutes=30),
        ),
        Generation(
            prompt="شركة تقنية للذكاء الاصطناعي",
            langue="ar",
            categorie="TECH",
            type_nom="societe",
            nom_genere="NoorAI",
            score=71.0,
            mode="B",
            created_at=base_date - timedelta(minutes=10),
        ),
    ]

    for gen in generations:
        session.add(gen)
    session.commit()

    for gen in generations:
        session.refresh(gen)

    # Votes : Veloria très appréciée, Solvita rejetée
    votes = [
        Feedback(generation_id=generations[0].id, vote_type="like"),
        Feedback(generation_id=generations[0].id, vote_type="like"),
        Feedback(generation_id=generations[0].id, vote_type="like"),
        Feedback(generation_id=generations[1].id, vote_type="like"),
        Feedback(generation_id=generations[1].id, vote_type="dislike"),
        Feedback(generation_id=generations[2].id, vote_type="dislike"),
        Feedback(generation_id=generations[2].id, vote_type="dislike"),
        Feedback(generation_id=generations[2].id, vote_type="dislike"),
        Feedback(generation_id=generations[3].id, vote_type="like"),
    ]
    for vote in votes:
        session.add(vote)

    favoris = [
        Favori(
            generation_id=generations[0].id,
            nom=generations[0].nom_genere,
            langue=generations[0].langue,
            categorie=generations[0].categorie,
            type_nom=generations[0].type_nom,
        ),
        Favori(
            generation_id=generations[3].id,
            nom=generations[3].nom_genere,
            langue=generations[3].langue,
            categorie=generations[3].categorie,
            type_nom=generations[3].type_nom,
        ),
    ]
    for fav in favoris:
        session.add(fav)

    session.commit()
    print(f"[init_db] {len(generations)} générations, {len(votes)} votes, {len(favoris)} favoris insérés.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialise la base SQLite NomGen.")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Insère des données d'exemple après création des tables.",
    )
    args = parser.parse_args()

    create_db_and_tables()
    print("[init_db] Tables créées (generations, feedback, favoris + tables existantes).")

    if args.seed:
        with Session(engine) as session:
            seed_sample_data(session)


if __name__ == "__main__":
    main()
