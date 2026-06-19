"""
Service de persistance automatique des noms générés.

Appelé après chaque génération réussie (Mode A et Mode B)
sans modifier la logique de génération elle-même.
"""
from typing import Any

from sqlmodel import Session

from app.models.feedback_models import Generation


def save_generated_names(
    session: Session,
    *,
    prompt: str,
    langue: str,
    categorie: str,
    type_nom: str,
    noms: list[Any],
    mode: str = "A",
) -> list[int]:
    """
    Enregistre chaque nom généré dans la table `generations`.

    Args:
        session: Session SQLModel active.
        prompt: Prompt utilisateur.
        langue: Code langue (fr, ar, en).
        categorie: Secteur / catégorie.
        type_nom: 'marque' ou 'societe'.
        noms: Liste de dicts {nom, score, ...} ou objets Pydantic.
        mode: 'A' (nanoGPT) ou 'B' (LLM).

    Returns:
        Liste des IDs créés (un par nom enregistré).
    """
    if not noms:
        return []

    created_ids: list[int] = []

    for item in noms:
        # Supporte dict (Mode A) et objets Pydantic (Mode B)
        if isinstance(item, dict):
            nom = item.get("nom", "")
            score = float(item.get("score", 0.0))
        else:
            nom = getattr(item, "nom", "")
            score = float(getattr(item, "score", 0.0))

        nom = str(nom).strip()
        if not nom:
            continue

        record = Generation(
            prompt=prompt,
            langue=langue,
            categorie=categorie,
            type_nom=type_nom,
            nom_genere=nom,
            score=score,
            mode=mode,
        )
        session.add(record)
        session.flush()  # Obtient l'ID sans commit (le router peut committer)
        created_ids.append(record.id)

    session.commit()
    return created_ids
