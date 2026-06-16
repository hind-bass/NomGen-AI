"""
Routes d'administration.
POST   /api/admin/users               — créer un utilisateur
GET    /api/admin/users               — lister les utilisateurs
PATCH  /api/admin/users/:id           — modifier un utilisateur (rôle, actif)
DELETE /api/admin/users/:id           — supprimer un utilisateur
GET    /api/admin/suggestions         — lister les suggestions avec filtrage
POST   /api/admin/suggestions/add     — ajouter une suggestion directe (vérification doublon)
PATCH  /api/admin/suggestions/:id     — valider/rejeter une suggestion
"""
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import get_current_admin
from app.models.db_models import Suggestion, User
from app.services.auth_service import hash_password

router = APIRouter(prefix="/api/admin", tags=["Administration"])

# Racine du dossier data/
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


# ─── Schémas ─────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "user"          # "user" | "admin"
    is_active: bool = True


class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserRead(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    created_at: str


class SuggestionDirectAdd(BaseModel):
    nom: str
    langue: str
    secteur: str
    type_nom: str = "marque"          # "marque" | "societe"


class SuggestionReview(BaseModel):
    action: str                         # "approve" | "reject"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _dataset_path(langue: str, secteur: str, type_nom: str) -> Path:
    """Calcule le chemin du fichier .txt cible selon langue/secteur/type."""
    cat  = secteur.lower().strip()
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


def _nom_existe_en_base(session: Session, nom: str, langue: str, secteur: str) -> bool:
    """Vérifie si le nom existe en base (approved ou pending)."""
    existing = session.exec(
        select(Suggestion).where(
            Suggestion.nom == nom,
            Suggestion.langue == langue,
            Suggestion.secteur == secteur,
            Suggestion.status.in_(["approved", "pending"]),
        )
    ).first()
    return existing is not None


def _ajouter_au_dataset(path: Path, nom: str):
    """Ajoute le nom approuvé au bon fichier .txt (crée les dossiers si nécessaire)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    nom_clean = nom.lower().strip()

    # Vérifier si n'existe pas déjà dans le fichier
    if not _nom_existe_dans_fichier(path, nom_clean):
        with open(path, "a", encoding="utf-8") as f:
            f.write(nom_clean + "\n")


# ─── Endpoints : Gestion des utilisateurs ─────────────────────────────────────

@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserRead)
def create_user(
    req: UserCreate,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    Créer un nouvel utilisateur (admin uniquement).
    """
    existing = session.exec(
        select(User).where(User.email == req.email)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte avec cet email existe déjà.",
        )

    if len(req.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le mot de passe doit contenir au moins 6 caractères.",
        )

    new_user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        role=req.role,
        is_active=req.is_active,
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return UserRead(
        id=new_user.id,
        email=new_user.email,
        role=new_user.role,
        is_active=new_user.is_active,
        created_at=new_user.created_at.isoformat(),
    )


@router.get("/users", response_model=list[UserRead])
def list_users(
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    Lister tous les utilisateurs (admin uniquement).
    """
    users = session.exec(select(User)).all()
    return [
        UserRead(
            id=u.id,
            email=u.email,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at.isoformat(),
        )
        for u in users
    ]


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    req: UserUpdate,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    Mettre à jour un utilisateur (admin uniquement).
    Peut changer le rôle ou le statut actif.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    if req.role is not None:
        if req.role not in ["user", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Le rôle doit être 'user' ou 'admin'.",
            )
        user.role = req.role

    if req.is_active is not None:
        user.is_active = req.is_active

    session.add(user)
    session.commit()
    session.refresh(user)

    return UserRead(
        id=user.id,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    Supprimer un utilisateur (admin uniquement).
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    # Empêcher la suppression du dernier admin
    admin_count = session.exec(
        select(User).where(User.role == "admin")
    ).all()
    if user.role == "admin" and len(admin_count) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer le dernier administrateur.",
        )

    session.delete(user)
    session.commit()


# ─── Endpoints : Gestion des suggestions ──────────────────────────────────────

@router.get("/suggestions")
def list_all_suggestions(
    status_filter: Optional[str] = None,  # "pending", "approved", "rejected"
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    Lister toutes les suggestions avec filtrage par statut (admin uniquement).
    """
    query = select(Suggestion)

    if status_filter:
        if status_filter not in ["pending", "approved", "rejected"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Statut invalide. Doit être 'pending', 'approved' ou 'rejected'.",
            )
        query = query.where(Suggestion.status == status_filter)

    suggestions = session.exec(query).all()

    return [
        {
            "id": s.id,
            "nom": s.nom,
            "langue": s.langue,
            "secteur": s.secteur,
            "type_nom": s.type_nom,
            "status": s.status,
            "user_id": s.user_id,
            "submitted_at": s.submitted_at.isoformat(),
            "reviewed_at": s.reviewed_at.isoformat() if s.reviewed_at else None,
        }
        for s in suggestions
    ]


@router.post("/suggestions/add", status_code=status.HTTP_201_CREATED)
def add_suggestion_direct(
    req: SuggestionDirectAdd,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    Ajouter une suggestion directement (sans modération).
    Vérifie si le nom existe déjà dans le dataset ou en base.
    Si valide : ajoute au dataset ET en base avec statut "approved".
    """
    nom_clean = req.nom.strip().lower()

    if len(nom_clean) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le nom doit contenir au moins 2 caractères.",
        )

    # Vérifier si le nom existe dans le fichier dataset
    dataset_file = _dataset_path(req.langue, req.secteur, req.type_nom)
    if _nom_existe_dans_fichier(dataset_file, nom_clean):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{nom_clean}' existe déjà dans le dataset {req.langue}/{req.type_nom}/{req.secteur}.",
        )

    # Vérifier si le nom existe en base (approved ou pending)
    if _nom_existe_en_base(session, nom_clean, req.langue, req.secteur):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{nom_clean}' est déjà enregistré pour cette langue/secteur.",
        )

    # Ajouter au fichier dataset
    _ajouter_au_dataset(dataset_file, nom_clean)

    # Créer l'entrée en base avec statut "approved"
    suggestion = Suggestion(
        user_id=admin.id,
        nom=nom_clean,
        langue=req.langue,
        secteur=req.secteur,
        type_nom=req.type_nom,
        status="approved",
        reviewed_at=datetime.utcnow(),
    )
    session.add(suggestion)
    session.commit()
    session.refresh(suggestion)

    return {
        "message": f"'{nom_clean}' ajouté avec succès.",
        "fichier": str(dataset_file.relative_to(DATA_DIR)),
        "suggestion_id": suggestion.id,
    }


@router.patch("/suggestions/{suggestion_id}")
def review_suggestion(
    suggestion_id: int,
    req: SuggestionReview,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    Valider ou rejeter une suggestion (admin uniquement).
    Si "approve" : ajoute au dataset et change le statut.
    Si "reject" : change le statut sans ajouter au dataset.
    """
    suggestion = session.get(Suggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion introuvable.")

    if suggestion.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cette suggestion a déjà été traitée (statut : {suggestion.status}).",
        )

    if req.action == "approve":
        # Vérifier que le nom n'existe pas déjà dans le dataset
        dataset_file = _dataset_path(suggestion.langue, suggestion.secteur, suggestion.type_nom)
        if _nom_existe_dans_fichier(dataset_file, suggestion.nom):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"'{suggestion.nom}' existe déjà dans le dataset.",
            )

        # Ajouter au dataset
        _ajouter_au_dataset(dataset_file, suggestion.nom)
        suggestion.status = "approved"

    elif req.action == "reject":
        suggestion.status = "rejected"
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="L'action doit être 'approve' ou 'reject'.",
        )

    suggestion.reviewed_at = datetime.utcnow()
    session.add(suggestion)
    session.commit()

    return {
        "message": f"Suggestion {req.action}d.",
        "suggestion_id": suggestion_id,
        "status": suggestion.status,
    }
