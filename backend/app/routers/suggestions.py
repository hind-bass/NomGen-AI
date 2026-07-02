"""
Routes pour les suggestions communautaires.
POST  /api/suggestions                  — soumettre un nom
GET   /api/suggestions                  — lister (admin : tous, user : les siennes)
PATCH /api/suggestions/:id/approve      — approuver (admin) → ajoute au .txt
PATCH /api/suggestions/:id/reject       — rejeter (admin)
"""
import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import get_current_user, get_current_admin
from app.models.db_models import Suggestion, User

router = APIRouter(prefix="/api/suggestions", tags=["Suggestions communautaires"])

# Racine du dossier data/
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


# ─── Schémas ─────────────────────────────────────────────────────────────────

class SuggestionCreate(BaseModel):
    nom: str
    categorie: str = "general"       # secteur : tech, food, luxe, general
    langue: str = "fr"
    type_nom: str = "marque"           # marque | societe (entreprise accepté)

    @classmethod
    def normalize_secteur(cls, value: str) -> str:
        mapping = {
            "tech": "tech", "food": "food", "luxe": "luxe", "general": "general",
            "tous": "general", "minimal": "general", "futuriste": "tech",
        }
        return mapping.get(value.lower().strip(), value.lower().strip())

    @classmethod
    def normalize_type(cls, value: str) -> str:
        v = value.lower().strip()
        if v in ("entreprise", "societe", "company"):
            return "societe"
        return "marque"


class SuggestionRead(BaseModel):
    id: int
    nom: str
    categorie: str
    langue: str
    type_nom: str
    status: str
    submitted_at: str


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _dataset_path(langue: str, categorie: str, type_nom: str) -> Path:
    """Calcule le chemin du fichier .txt cible selon langue/catégorie/type."""
    cat  = categorie.lower().strip()
    typ  = type_nom.lower().strip()
    lang = langue.lower().strip()
    return DATA_DIR / lang / typ / f"{cat}.txt"


def _nom_existe_dans_fichier(path: Path, nom: str) -> bool:
    """Vérifie si le nom est déjà dans le fichier dataset."""
    if not path.exists():
        return False
    with open(path, encoding="utf-8") as f:
        noms_existants = {line.strip().lower() for line in f if line.strip()}
    return nom.lower().strip() in noms_existants


def _nom_existe_dans_dataset(langue: str, type_nom: str, nom: str) -> bool:
    """Vérifie si le nom existe déjà dans un fichier du dossier data/{lang}/{type}/."""
    type_dir = DATA_DIR / langue.lower().strip() / type_nom.lower().strip()
    if not type_dir.is_dir():
        return False
    for path in type_dir.glob("*.txt"):
        if _nom_existe_dans_fichier(path, nom):
            return True
    return False


def _ajouter_au_dataset(path: Path, nom: str):
    """Ajoute le nom approuvé au bon fichier .txt (crée les dossiers si nécessaire)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(nom.lower().strip() + "\n")


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SuggestionRead)
def submit_suggestion(
    req: SuggestionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Soumettre un nouveau nom pour modération.
    Retourne 409 si le nom existe déjà dans le dataset ou est en attente.
    """
    nom_clean = req.nom.strip().lower()
    if len(nom_clean) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le nom doit contenir au moins 2 caractères."
        )

    secteur = SuggestionCreate.normalize_secteur(req.categorie)
    type_nom = SuggestionCreate.normalize_type(req.type_nom)
    langue = req.langue.lower().strip()[:2]
    if langue not in ("fr", "ar"):
        langue = "fr"

    # Vérifier si déjà dans le dossier data/
    if _nom_existe_dans_dataset(langue, type_nom, nom_clean):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{nom_clean}' existe déjà dans la base de données ({langue}/{type_nom})."
        )

    # Vérifier si déjà approuvé en base
    already_approved = session.exec(
        select(Suggestion).where(
            Suggestion.nom == nom_clean,
            Suggestion.langue == langue,
            Suggestion.secteur == secteur,
            Suggestion.status == "approved",
        )
    ).first()
    if already_approved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{nom_clean}' est déjà validé et présent dans la base."
        )

    # Vérifier si déjà soumis et en attente
    existing = session.exec(
        select(Suggestion).where(
            Suggestion.nom == nom_clean,
            Suggestion.langue == langue,
            Suggestion.status == "pending",
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{nom_clean}' est déjà en attente de validation par l'administrateur."
        )

    suggestion = Suggestion(
        user_id=current_user.id,
        nom=nom_clean,
        langue=langue,
        secteur=secteur,
        type_nom=type_nom,
        status="pending",
    )
    session.add(suggestion)
    session.commit()
    session.refresh(suggestion)

    return SuggestionRead(
        id=suggestion.id,
        nom=suggestion.nom,
        categorie=suggestion.secteur,
        langue=suggestion.langue,
        type_nom=suggestion.type_nom,
        status=suggestion.status,
        submitted_at=suggestion.submitted_at.isoformat(),
    )


@router.get("/", response_model=list[SuggestionRead])
def list_suggestions(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    - Admin : voit toutes les suggestions (pour le dashboard de modération).
    - User : voit seulement les siennes.
    """
    if current_user.role == "admin":
        results = session.exec(select(Suggestion)).all()
    else:
        results = session.exec(
            select(Suggestion).where(Suggestion.user_id == current_user.id)
        ).all()

    return [
        SuggestionRead(
            id=s.id,
            nom=s.nom,
            categorie=s.secteur,
            langue=s.langue,
            type_nom=s.type_nom,
            status=s.status,
            submitted_at=s.submitted_at.isoformat(),
        )
        for s in results
    ]


@router.patch("/{suggestion_id}/approve")
def approve_suggestion(
    suggestion_id: int,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
   
    suggestion = session.get(Suggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion introuvable.")
    if suggestion.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cette suggestion a déjà été traitée (statut : {suggestion.status})."
        )

    dataset_file = _dataset_path(suggestion.langue, suggestion.secteur, suggestion.type_nom)
    if _nom_existe_dans_dataset(suggestion.langue, suggestion.type_nom, suggestion.nom):
        suggestion.status = "rejected"
        suggestion.reviewed_at = datetime.utcnow()
        session.add(suggestion)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{suggestion.nom}' existe déjà dans data/{suggestion.langue}/{suggestion.type_nom}/ — suggestion rejetée."
        )

    # Ajouter au dataset
    _ajouter_au_dataset(dataset_file, suggestion.nom)

    # Mettre à jour le statut
    suggestion.status = "approved"
    suggestion.reviewed_at = datetime.utcnow()
    session.add(suggestion)
    session.commit()

    return {
        "message": f"'{suggestion.nom}' approuvé et ajouté dans {dataset_file.relative_to(DATA_DIR)}.",
        "fichier": str(dataset_file),
    }


@router.patch("/{suggestion_id}/reject")
def reject_suggestion(
    suggestion_id: int,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    Rejette une suggestion (admin uniquement).
    → Statut "rejected" en DB, rien ajouté au dataset.
    """
    suggestion = session.get(Suggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion introuvable.")
    if suggestion.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cette suggestion a déjà été traitée (statut : {suggestion.status})."
        )

    suggestion.status = "rejected"
    suggestion.reviewed_at = datetime.utcnow()
    session.add(suggestion)
    session.commit()

    return {"message": f"'{suggestion.nom}' rejeté.", "id": suggestion_id}