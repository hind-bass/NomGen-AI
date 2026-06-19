"""
Service d'analyse des votes (likes, dislikes, favoris).

Fournit :
  - Enregistrement des votes
  - Calcul du score (likes - dislikes)
  - Classements des noms les plus appréciés / rejetés
  - Statistiques agrégées
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlmodel import Session, func, select

from app.models.feedback_models import Favori, Feedback, Generation
from app.schemas.feedback_schemas import (
    FeedbackStatsResponse,
    NameScoreItem,
    VoteStatsItem,
)


class FeedbackService:
    """Couche métier pour le système de feedback."""

    def __init__(self, session: Session):
        self.session = session

    # ── Helpers internes ─────────────────────────────────────────────────────

    def _get_generation_or_404(self, generation_id: int) -> Generation:
        """Récupère une génération ou lève HTTP 404."""
        generation = self.session.get(Generation, generation_id)
        if not generation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Génération #{generation_id} introuvable.",
            )
        return generation

    def _count_votes(self, generation_id: int) -> tuple[int, int]:
        """Compte les likes et dislikes pour une génération."""
        likes = self.session.exec(
            select(func.count(Feedback.id)).where(
                Feedback.generation_id == generation_id,
                Feedback.vote_type == "like",
            )
        ).one()
        dislikes = self.session.exec(
            select(func.count(Feedback.id)).where(
                Feedback.generation_id == generation_id,
                Feedback.vote_type == "dislike",
            )
        ).one()
        return int(likes), int(dislikes)

    # ── Votes ────────────────────────────────────────────────────────────────

    def add_vote(
        self,
        generation_id: int,
        vote_type: str,
        user_id: Optional[int] = None,
    ) -> VoteStatsItem:
        """
        Enregistre un like ou dislike.

        Si l'utilisateur a déjà voté sur cette génération, le vote est mis à jour.
        """
        self._get_generation_or_404(generation_id)

        if vote_type not in ("like", "dislike"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="vote_type doit être 'like' ou 'dislike'.",
            )

        # Évite les doublons : un seul vote par (generation, user) ou par generation si anonyme
        query = select(Feedback).where(Feedback.generation_id == generation_id)
        if user_id is not None:
            query = query.where(Feedback.user_id == user_id)
        else:
            query = query.where(Feedback.user_id.is_(None))

        existing = self.session.exec(query).first()

        if existing:
            if existing.vote_type == vote_type:
                likes, dislikes = self._count_votes(generation_id)
                return VoteStatsItem(
                    generation_id=generation_id,
                    nom_genere=self.session.get(Generation, generation_id).nom_genere,
                    likes=likes,
                    dislikes=dislikes,
                    score=likes - dislikes,
                )
            existing.vote_type = vote_type
            self.session.add(existing)
        else:
            self.session.add(
                Feedback(
                    generation_id=generation_id,
                    vote_type=vote_type,
                    user_id=user_id,
                )
            )

        self.session.commit()

        likes, dislikes = self._count_votes(generation_id)
        generation = self.session.get(Generation, generation_id)
        return VoteStatsItem(
            generation_id=generation_id,
            nom_genere=generation.nom_genere,
            likes=likes,
            dislikes=dislikes,
            score=likes - dislikes,
        )

    # ── Favoris ──────────────────────────────────────────────────────────────

    def add_favori(
        self,
        generation_id: int,
        user_id: Optional[int] = None,
    ) -> Favori:
        """Ajoute un nom aux favoris à partir de son generation_id."""
        generation = self._get_generation_or_404(generation_id)

        query = select(Favori).where(Favori.generation_id == generation_id)
        if user_id is not None:
            query = query.where(Favori.user_id == user_id)
        else:
            query = query.where(Favori.user_id.is_(None))

        if self.session.exec(query).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"'{generation.nom_genere}' est déjà dans les favoris.",
            )

        favori = Favori(
            generation_id=generation_id,
            user_id=user_id,
            nom=generation.nom_genere,
            langue=generation.langue,
            categorie=generation.categorie,
            type_nom=generation.type_nom,
        )
        self.session.add(favori)
        self.session.commit()
        self.session.refresh(favori)
        return favori

    def list_favoris(self, user_id: Optional[int] = None) -> list[Favori]:
        """Liste tous les favoris (filtrés par user_id si fourni)."""
        query = select(Favori).order_by(Favori.created_at.desc())
        if user_id is not None:
            query = query.where(Favori.user_id == user_id)
        return list(self.session.exec(query).all())

    # ── Analyse et statistiques ──────────────────────────────────────────────

    def compute_score(self, generation_id: int) -> int:
        """Calcule le score d'une génération : likes - dislikes."""
        likes, dislikes = self._count_votes(generation_id)
        return likes - dislikes

    def get_most_liked(self, limit: int = 10) -> list[NameScoreItem]:
        """Retourne les noms les plus appréciés (score décroissant)."""
        return self._rank_names(order_desc=True, limit=limit)

    def get_most_disliked(self, limit: int = 10) -> list[NameScoreItem]:
        """Retourne les noms les plus rejetés (score croissant)."""
        return self._rank_names(order_desc=False, limit=limit)

    def _rank_names(self, *, order_desc: bool, limit: int) -> list[NameScoreItem]:
        """Agrège les votes par génération et trie par score."""
        generations = list(self.session.exec(select(Generation)).all())
        ranked: list[NameScoreItem] = []

        for gen in generations:
            likes, dislikes = self._count_votes(gen.id)
            if likes == 0 and dislikes == 0:
                continue
            ranked.append(
                NameScoreItem(
                    generation_id=gen.id,
                    nom_genere=gen.nom_genere,
                    langue=gen.langue,
                    categorie=gen.categorie,
                    type_nom=gen.type_nom,
                    likes=likes,
                    dislikes=dislikes,
                    score=likes - dislikes,
                )
            )

        ranked.sort(key=lambda x: x.score, reverse=order_desc)
        return ranked[:limit]

    def get_stats(self, top_n: int = 5) -> FeedbackStatsResponse:
        """Statistiques globales du système de feedback."""
        total_generations = self.session.exec(
            select(func.count(Generation.id))
        ).one()

        total_likes = self.session.exec(
            select(func.count(Feedback.id)).where(Feedback.vote_type == "like")
        ).one()
        total_dislikes = self.session.exec(
            select(func.count(Feedback.id)).where(Feedback.vote_type == "dislike")
        ).one()

        total_likes = int(total_likes)
        total_dislikes = int(total_dislikes)

        # Agrégation par langue
        par_langue: dict[str, dict[str, int]] = {}
        for langue, vote_type, count in self.session.exec(
            select(Generation.langue, Feedback.vote_type, func.count(Feedback.id))
            .join(Feedback, Feedback.generation_id == Generation.id)
            .group_by(Generation.langue, Feedback.vote_type)
        ).all():
            par_langue.setdefault(langue, {"likes": 0, "dislikes": 0})
            par_langue[langue][f"{vote_type}s"] = int(count)

        # Agrégation par catégorie
        par_categorie: dict[str, dict[str, int]] = {}
        for categorie, vote_type, count in self.session.exec(
            select(Generation.categorie, Feedback.vote_type, func.count(Feedback.id))
            .join(Feedback, Feedback.generation_id == Generation.id)
            .group_by(Generation.categorie, Feedback.vote_type)
        ).all():
            par_categorie.setdefault(categorie, {"likes": 0, "dislikes": 0})
            par_categorie[categorie][f"{vote_type}s"] = int(count)

        return FeedbackStatsResponse(
            total_generations=int(total_generations),
            total_likes=total_likes,
            total_dislikes=total_dislikes,
            score_global=total_likes - total_dislikes,
            plus_apprecies=self.get_most_liked(limit=top_n),
            plus_rejetes=self.get_most_disliked(limit=top_n),
            par_langue=par_langue,
            par_categorie=par_categorie,
        )
