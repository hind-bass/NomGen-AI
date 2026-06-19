"""
Export des datasets de fine-tuning depuis SQLite.

Sources de données positives :
  - Générations likées (feedback)
  - Favoris
  - Réservations payées

Sources négatives :
  - Générations dislikées

Formats exportés : jsonl (messages), alpaca, csv
"""
import csv
import io
import json
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models.db_models import Reservation
from app.models.feedback_models import Favori, Feedback, Generation
from app.services.dataset_loader_service import append_name_to_dataset, count_dataset_names, normalize_secteur


class TrainingDatasetService:
    """Construit et exporte des datasets pour le fine-tuning continu."""

    def __init__(self, session: Session):
        self.session = session

    def _system_prompt_fr(self, type_nom: str, categorie: str) -> str:
        return (
            f"Tu es un expert en naming. Génère des noms de {type_nom} "
            f"dans le secteur {categorie}. Réponds en JSON uniquement."
        )

    def _system_prompt_ar(self, type_nom: str, categorie: str) -> str:
        return (
            f"أنت خبير في تسمية العلامات. ولّد أسماء {type_nom} "
            f"في قطاع {categorie}. أجب بصيغة JSON فقط."
        )

    def _collect_positive_samples(
        self,
        langue: Optional[str] = None,
        categorie: Optional[str] = None,
    ) -> list[dict]:
        """Collecte les échantillons positifs depuis SQLite."""
        samples: dict[int, dict] = {}

        # Générations likées
        query = (
            select(Generation)
            .join(Feedback, Feedback.generation_id == Generation.id)
            .where(Feedback.vote_type == "like")
        )
        if langue:
            query = query.where(Generation.langue == langue)
        if categorie:
            query = query.where(Generation.categorie == categorie)

        for gen in self.session.exec(query).all():
            samples[gen.id] = {
                "prompt": gen.prompt,
                "langue": gen.langue,
                "categorie": gen.categorie,
                "type_nom": gen.type_nom,
                "nom": gen.nom_genere,
                "source": "like",
            }

        # Favoris
        fav_query = select(Favori, Generation).join(
            Generation, Generation.id == Favori.generation_id
        )
        if langue:
            fav_query = fav_query.where(Favori.langue == langue)
        if categorie:
            fav_query = fav_query.where(Favori.categorie == categorie)

        for fav, gen in self.session.exec(fav_query).all():
            if gen.id not in samples:
                samples[gen.id] = {
                    "prompt": gen.prompt,
                    "langue": gen.langue,
                    "categorie": gen.categorie,
                    "type_nom": gen.type_nom,
                    "nom": fav.nom,
                    "source": "favori",
                }

        # Réservations payées — associer au prompt le plus proche si possible
        res_query = select(Reservation).where(Reservation.is_paid == True)  # noqa: E712
        if langue:
            res_query = res_query.where(Reservation.langue == langue)
        if categorie:
            res_query = res_query.where(Reservation.secteur == categorie)

        for res in self.session.exec(res_query).all():
            key = f"res_{res.id}"
            samples[key] = {
                "prompt": f"Réservation premium du nom {res.nom}",
                "langue": res.langue,
                "categorie": res.secteur,
                "type_nom": "marque",
                "nom": res.nom,
                "source": "reservation",
            }

        return list(samples.values())

    def _collect_negative_samples(
        self,
        langue: Optional[str] = None,
        categorie: Optional[str] = None,
    ) -> list[dict]:
        """Collecte les échantillons négatifs (dislikes)."""
        query = (
            select(Generation)
            .join(Feedback, Feedback.generation_id == Generation.id)
            .where(Feedback.vote_type == "dislike")
        )
        if langue:
            query = query.where(Generation.langue == langue)
        if categorie:
            query = query.where(Generation.categorie == categorie)

        return [
            {
                "prompt": gen.prompt,
                "langue": gen.langue,
                "categorie": gen.categorie,
                "type_nom": gen.type_nom,
                "nom": gen.nom_genere,
                "source": "dislike",
            }
            for gen in self.session.exec(query).all()
        ]

    def get_stats(self) -> dict:
        """Statistiques sur les données disponibles pour le fine-tuning."""
        positives = self._collect_positive_samples()
        negatives = self._collect_negative_samples()
        static = count_dataset_names()

        by_langue: dict = {"fr": 0, "ar": 0}
        by_source: dict = {}
        for s in positives:
            by_langue[s["langue"]] = by_langue.get(s["langue"], 0) + 1
            by_source[s["source"]] = by_source.get(s["source"], 0) + 1

        return {
            "positive_samples": len(positives),
            "negative_samples": len(negatives),
            "static_dataset_names": static["total"],
            "static_files": static["files"],
            "by_langue": by_langue,
            "by_source": by_source,
            "ready_for_finetuning": len(positives) >= 50,
            "recommended_min_samples": 50,
        }

    def export_jsonl(
        self,
        langue: Optional[str] = None,
        categorie: Optional[str] = None,
        include_negative: bool = False,
    ) -> str:
        """
        Export JSONL format messages (compatible Llama 3.1 / Qwen 2.5 fine-tuning).
        """
        lines: list[str] = []
        positives = self._collect_positive_samples(langue, categorie)

        # Grouper par (prompt, langue, categorie, type_nom) → liste de noms
        groups: dict[tuple, list[str]] = {}
        for s in positives:
            key = (s["prompt"], s["langue"], s["categorie"], s["type_nom"])
            groups.setdefault(key, []).append(s["nom"])

        for (prompt, lang, cat, typ), noms in groups.items():
            unique_noms = list(dict.fromkeys(noms))
            if lang == "ar":
                system = self._system_prompt_ar(typ, cat)
                user = f"الوصف: {prompt}\nولّد أسماء {typ} في قطاع {cat}."
            else:
                system = self._system_prompt_fr(typ, cat)
                user = f"Contexte : {prompt}\nGénère des noms de {typ} secteur {cat}."

            entry = {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                    {"role": "assistant", "content": json.dumps(unique_noms, ensure_ascii=False)},
                ],
                "metadata": {
                    "langue": lang,
                    "categorie": cat,
                    "type_nom": typ,
                    "exported_at": datetime.utcnow().isoformat(),
                },
            }
            lines.append(json.dumps(entry, ensure_ascii=False))

        if include_negative:
            for s in self._collect_negative_samples(langue, categorie):
                entry = {
                    "messages": [
                        {"role": "system", "content": "Noms rejetés — ne pas reproduire ce style."},
                        {"role": "user", "content": s["prompt"]},
                        {"role": "assistant", "content": json.dumps([s["nom"]], ensure_ascii=False)},
                    ],
                    "metadata": {"label": "negative", "langue": s["langue"]},
                }
                lines.append(json.dumps(entry, ensure_ascii=False))

        return "\n".join(lines)

    def export_alpaca(
        self,
        langue: Optional[str] = None,
        categorie: Optional[str] = None,
    ) -> str:
        """Export format Alpaca (instruction/input/output)."""
        lines: list[str] = []
        for s in self._collect_positive_samples(langue, categorie):
            if s["langue"] == "ar":
                instruction = f"ولّد اسم {s['type_nom']} في قطاع {s['categorie']}"
            else:
                instruction = f"Génère un nom de {s['type_nom']} secteur {s['categorie']}"
            entry = {
                "instruction": instruction,
                "input": s["prompt"],
                "output": s["nom"],
            }
            lines.append(json.dumps(entry, ensure_ascii=False))
        return "\n".join(lines)

    def export_csv(
        self,
        langue: Optional[str] = None,
        categorie: Optional[str] = None,
    ) -> str:
        """Export CSV pour analyse ou import manuel."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["prompt", "langue", "categorie", "type_nom", "nom", "source", "label"])
        for s in self._collect_positive_samples(langue, categorie):
            writer.writerow([s["prompt"], s["langue"], s["categorie"], s["type_nom"], s["nom"], s["source"], "positive"])
        for s in self._collect_negative_samples(langue, categorie):
            writer.writerow([s["prompt"], s["langue"], s["categorie"], s["type_nom"], s["nom"], s["source"], "negative"])
        return output.getvalue()

    def sync_positive_to_static_datasets(self) -> dict:
        """
        Synchronise les noms validés (likes, favoris, réservations payées)
        vers les fichiers data/ pour enrichir le few-shot et préparer le fine-tuning.
        """
        added = 0
        skipped = 0
        for s in self._collect_positive_samples():
            ok = append_name_to_dataset(
                s["langue"],
                s["categorie"],
                s["type_nom"],
                s["nom"],
            )
            if ok:
                added += 1
            else:
                skipped += 1
        return {"added": added, "skipped": skipped, "message": f"{added} noms ajoutés aux datasets statiques."}
