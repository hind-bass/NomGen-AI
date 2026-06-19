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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import get_current_admin
from app.models.db_models import Reservation, Suggestion, User
from app.services.auth_service import hash_password
from app.services.training_dataset_service import TrainingDatasetService
from app.services.local_naming_service import LOCAL_MODELS
from app.services.dataset_loader_service import count_dataset_names

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


class ReservationAdminRead(BaseModel):
    id: int
    nom: str
    langue: str
    secteur: str
    user_id: int
    user_email: str
    stripe_url: str | None
    expires_at: str | None
    is_paid: bool
    created_at: str
    status: str                         # "pending" | "paid" | "expired"
    forfait: str = "free"
    client_nom: str | None = None
    client_prenom: str | None = None
    client_email: str | None = None
    card_last4: str | None = None
    card_expiry: str | None = None
    payment_status: str = "pending"


class ReservationStats(BaseModel):
    total: int
    pending: int
    paid: int
    expired: int


class ReservationUpdate(BaseModel):
    action: str                         # "mark_paid" | "mark_unpaid" | "extend"
    days: Optional[int] = 30            # utilisé avec action "extend"


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


def _nom_existe_dans_dataset(langue: str, type_nom: str, nom: str) -> bool:
    """Vérifie si le nom existe déjà dans data/{lang}/{type}/."""
    type_dir = DATA_DIR / langue.lower().strip() / type_nom.lower().strip()
    if not type_dir.is_dir():
        return False
    for path in type_dir.glob("*.txt"):
        if _nom_existe_dans_fichier(path, nom):
            return True
    return False


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


def _reservation_status(reservation: Reservation) -> str:
    """Calcule le statut métier d'une réservation."""
    if reservation.is_paid:
        return "paid"
    if reservation.expires_at and reservation.expires_at <= datetime.utcnow():
        return "expired"
    return "pending"


def _reservation_to_admin_read(reservation: Reservation, user_email: str) -> ReservationAdminRead:
    """Sérialise une réservation pour l'espace admin."""
    return ReservationAdminRead(
        id=reservation.id,
        nom=reservation.nom,
        langue=reservation.langue,
        secteur=reservation.secteur,
        user_id=reservation.user_id,
        user_email=user_email,
        stripe_url=reservation.stripe_url,
        expires_at=reservation.expires_at.isoformat() if reservation.expires_at else None,
        is_paid=reservation.is_paid,
        created_at=reservation.created_at.isoformat(),
        status=_reservation_status(reservation),
        forfait=getattr(reservation, "forfait", "free") or "free",
        client_nom=getattr(reservation, "client_nom", None),
        client_prenom=getattr(reservation, "client_prenom", None),
        client_email=getattr(reservation, "client_email", None),
        card_last4=getattr(reservation, "card_last4", None),
        card_expiry=getattr(reservation, "card_expiry", None),
        payment_status=getattr(reservation, "payment_status", "pending") or "pending",
    )


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
        dataset_file = _dataset_path(suggestion.langue, suggestion.secteur, suggestion.type_nom)
        if _nom_existe_dans_dataset(suggestion.langue, suggestion.type_nom, suggestion.nom):
            suggestion.status = "rejected"
            suggestion.reviewed_at = datetime.utcnow()
            session.add(suggestion)
            session.commit()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"'{suggestion.nom}' existe déjà dans data/{suggestion.langue}/{suggestion.type_nom}/ — suggestion rejetée.",
            )

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


# ─── Endpoints : Gestion des réservations ─────────────────────────────────────

@router.get("/reservations/stats", response_model=ReservationStats)
def reservation_stats(
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """Statistiques globales des réservations (admin uniquement)."""
    reservations = session.exec(select(Reservation)).all()
    stats = {"total": 0, "pending": 0, "paid": 0, "expired": 0}
    for r in reservations:
        stats["total"] += 1
        stats[_reservation_status(r)] += 1
    return ReservationStats(**stats)


@router.get("/reservations", response_model=list[ReservationAdminRead])
def list_all_reservations(
    status_filter: Optional[str] = None,   # pending | paid | expired
    search: Optional[str] = None,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    Lister toutes les demandes de réservation (admin uniquement).
    Filtres optionnels : statut et recherche par nom ou email utilisateur.
    """
    if status_filter and status_filter not in ["pending", "paid", "expired"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Statut invalide. Doit être 'pending', 'paid' ou 'expired'.",
        )

    rows = session.exec(
        select(Reservation, User.email)
        .join(User, User.id == Reservation.user_id)
        .order_by(Reservation.created_at.desc())
    ).all()

    results: list[ReservationAdminRead] = []
    search_lower = search.lower().strip() if search else None

    for reservation, user_email in rows:
        item = _reservation_to_admin_read(reservation, user_email)

        if status_filter and item.status != status_filter:
            continue

        if search_lower:
            if search_lower not in item.nom.lower() and search_lower not in user_email.lower():
                continue

        results.append(item)

    return results


@router.patch("/reservations/{reservation_id}", response_model=ReservationAdminRead)
def update_reservation(
    reservation_id: int,
    req: ReservationUpdate,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    Mettre à jour une réservation (admin uniquement).
    Actions : mark_paid, mark_unpaid, extend (prolonger l'expiration).
    """
    reservation = session.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Réservation introuvable.")

    user = session.get(User, reservation.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur associé introuvable.")

    if req.action == "mark_paid":
        reservation.is_paid = True
        reservation.payment_status = "validated"
    elif req.action == "mark_unpaid":
        reservation.is_paid = False
        reservation.payment_status = "pending"
    elif req.action == "extend":
        days = req.days or 30
        if days < 1 or days > 365:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La durée doit être entre 1 et 365 jours.",
            )
        base = reservation.expires_at or datetime.utcnow()
        if base < datetime.utcnow():
            base = datetime.utcnow()
        reservation.expires_at = base + timedelta(days=days)
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Action invalide. Doit être 'mark_paid', 'mark_unpaid' ou 'extend'.",
        )

    session.add(reservation)
    session.commit()
    session.refresh(reservation)

    return _reservation_to_admin_read(reservation, user.email)


@router.delete("/reservations/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reservation_admin(
    reservation_id: int,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """Supprimer une réservation (admin uniquement)."""
    reservation = session.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Réservation introuvable.")
    session.delete(reservation)
    session.commit()


# ─── Endpoints : Datasets & Fine-tuning ───────────────────────────────────────

@router.get("/training/stats")
def training_stats(
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    Statistiques sur les données collectées (likes, favoris, réservations)
    disponibles pour le fine-tuning continu.
    """
    service = TrainingDatasetService(session)
    stats = service.get_stats()
    stats["local_models"] = LOCAL_MODELS
    stats["static_breakdown"] = count_dataset_names()
    return stats


@router.get("/training/local-models")
def list_local_models(admin: User = Depends(get_current_admin)):
    """Liste des modèles LLM open source locaux recommandés (Ollama)."""
    return {
        "models": [
            {"key": k, **v} for k, v in LOCAL_MODELS.items()
        ],
        "setup": [
            "1. Installer Ollama : https://ollama.com",
            "2. Télécharger un modèle : ollama pull llama3.1",
            "3. Utiliser Mode B avec model_key : ollama-llama31",
        ],
    }


@router.get("/training/export")
def export_training_dataset(
    format: str = "jsonl",
    langue: Optional[str] = None,
    categorie: Optional[str] = None,
    include_negative: bool = False,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    Exporte un dataset de fine-tuning depuis SQLite.
    Formats : jsonl (Llama/Qwen), alpaca, csv
    """
    if format not in ("jsonl", "alpaca", "csv"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Format invalide. Utilisez : jsonl, alpaca, csv.",
        )
    if langue and langue not in ("fr", "ar"):
        raise HTTPException(status_code=422, detail="Langue invalide : fr ou ar.")

    service = TrainingDatasetService(session)

    if format == "jsonl":
        content = service.export_jsonl(langue, categorie, include_negative)
        filename = f"nomgen_finetuning_{langue or 'all'}.jsonl"
        media = "application/jsonl"
    elif format == "alpaca":
        content = service.export_alpaca(langue, categorie)
        filename = f"nomgen_alpaca_{langue or 'all'}.jsonl"
        media = "application/jsonl"
    else:
        content = service.export_csv(langue, categorie)
        filename = f"nomgen_training_{langue or 'all'}.csv"
        media = "text/csv"

    if not content.strip():
        raise HTTPException(
            status_code=404,
            detail="Aucune donnée disponible. Générez des noms et collectez des likes/favoris.",
        )

    return PlainTextResponse(
        content=content,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/training/sync-datasets")
def sync_training_to_static_datasets(
    admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    """
    Synchronise les noms validés (likes, favoris, réservations payées)
    vers les fichiers data/ pour enrichir le few-shot et préparer le fine-tuning.
    """
    service = TrainingDatasetService(session)
    return service.sync_positive_to_static_datasets()
