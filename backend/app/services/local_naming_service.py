"""
Service de spécialisation des LLM locaux (Ollama) pour le naming FR/AR.

Combine :
  - Few-shot depuis les datasets statiques (data/)
  - Exemples positifs depuis SQLite (likes, favoris, réservations payées)
  - Exemples négatifs depuis SQLite (dislikes)
"""
from sqlmodel import Session, select, func

from app.models.db_models import Reservation
from app.models.feedback_models import Favori, Feedback, Generation
from app.services.dataset_loader_service import load_few_shot_examples, normalize_secteur, normalize_type

# Modèles Ollama open source recommandés pour le naming
LOCAL_MODELS = {
    "llama3.1": {
        "ollama_id": "llama3.1",
        "label": "Llama 3.1 8B",
        "langues": ["fr", "ar"],
        "pull_cmd": "ollama pull llama3.1",
    },
    "qwen2.5": {
        "ollama_id": "qwen2.5",
        "label": "Qwen 2.5 7B",
        "langues": ["fr", "ar"],
        "pull_cmd": "ollama pull qwen2.5",
    },
    "nomgen-qwen25": {
        "ollama_id": "nomgen-qwen25",
        "label": "NomGen Qwen 2.5 (fine-tuné)",
        "langues": ["fr", "ar"],
        "pull_cmd": "ollama create nomgen-qwen25 -f Modelfile",
    },
    "mistral": {
        "ollama_id": "mistral",
        "label": "Mistral 7B",
        "langues": ["fr"],
        "pull_cmd": "ollama pull mistral",
    },
}


class LocalNamingService:
    """Construit des prompts enrichis pour la génération de noms via Ollama."""

    def __init__(self, session: Session):
        self.session = session

    def _get_liked_names(
        self,
        langue: str,
        categorie: str,
        type_nom: str,
        limit: int = 6,
    ) -> list[str]:
        """Noms appréciés (likes) pour ce contexte."""
        rows = self.session.exec(
            select(Generation.nom_genere)
            .join(Feedback, Feedback.generation_id == Generation.id)
            .where(
                Feedback.vote_type == "like",
                Generation.langue == langue,
                func.lower(Generation.categorie) == normalize_secteur(categorie),
                Generation.type_nom == normalize_type(type_nom),
            )
            .distinct()
            .limit(limit)
        ).all()
        return [r for r in rows if r]

    def _get_favori_names(
        self,
        langue: str,
        categorie: str,
        type_nom: str,
        limit: int = 4,
    ) -> list[str]:
        """Noms en favoris pour ce contexte."""
        rows = self.session.exec(
            select(Favori.nom)
            .where(
                Favori.langue == langue,
                func.lower(Favori.categorie) == normalize_secteur(categorie),
                Favori.type_nom == normalize_type(type_nom),
            )
            .distinct()
            .limit(limit)
        ).all()
        return [r for r in rows if r]

    def _get_reserved_names(
        self,
        langue: str,
        categorie: str,
        limit: int = 4,
    ) -> list[str]:
        """Noms réservés (payés = signal fort de qualité)."""
        rows = self.session.exec(
            select(Reservation.nom)
            .where(
                Reservation.langue == langue,
                func.lower(Reservation.secteur) == normalize_secteur(categorie),
                Reservation.is_paid == True,  # noqa: E712
            )
            .distinct()
            .limit(limit)
        ).all()
        return [r for r in rows if r]

    def _get_disliked_names(
        self,
        langue: str,
        categorie: str,
        type_nom: str,
        limit: int = 4,
    ) -> list[str]:
        """Noms rejetés par les utilisateurs (à éviter)."""
        rows = self.session.exec(
            select(Generation.nom_genere)
            .join(Feedback, Feedback.generation_id == Generation.id)
            .where(
                Feedback.vote_type == "dislike",
                Generation.langue == langue,
                func.lower(Generation.categorie) == normalize_secteur(categorie),
                Generation.type_nom == normalize_type(type_nom),
            )
            .distinct()
            .limit(limit)
        ).all()
        return [r for r in rows if r]

    def build_specialized_system_prompt(
        self,
        langue: str,
        type_nom: str,
        secteur: str,
        style: str,
    ) -> str:
        """
        Prompt système enrichi avec few-shot et retours utilisateurs.
        Utilisé par OllamaProvider (Llama 3.1, Qwen 2.5, Mistral).
        """
        few_shot = load_few_shot_examples(langue, secteur, type_nom, limit=8)
        liked = self._get_liked_names(langue, secteur, type_nom)
        favoris = self._get_favori_names(langue, secteur, type_nom)
        reserved = self._get_reserved_names(langue, secteur)
        disliked = self._get_disliked_names(langue, secteur, type_nom)

        positive = list(dict.fromkeys(liked + favoris + reserved))[:10]
        negative = disliked[:6]

        typ = normalize_type(type_nom)
        cat = normalize_secteur(secteur)

        if langue == "ar":
            base = f"""أنت خبير متخصص في تسمية العلامات التجارية والشركات العربية.
قم بتوليد أسماء {typ} في قطاع {cat}.
القواعد:
- 3 إلى 12 حرفاً، سهل النطق، أصلي، لا يشبه العلامات الشهيرة
- الأسلوب: {style}
- أجب فقط بقائمة JSON: ["اسم1", "اسم2", ...]"""
            if few_shot:
                base += f"\n\nأمثلة من قاعدة البيانات: {', '.join(few_shot[:6])}"
            if positive:
                base += f"\n\nأسماء محبوبة من المستخدمين: {', '.join(positive)}"
            if negative:
                base += f"\n\nتجنب هذه الأسماء المرفوضة: {', '.join(negative)}"
            return base

        base = f"""Tu es un expert spécialisé en naming de marques et sociétés françaises.
Génère des noms de {typ} dans le secteur {cat}.
Règles :
- 3 à 12 caractères, mémorable, prononçable, original
- Style : {style}
- Réponds UNIQUEMENT avec une liste JSON : ["nom1", "nom2", ...]"""
        if few_shot:
            base += f"\n\nExemples de notre dataset : {', '.join(few_shot[:6])}"
        if positive:
            base += f"\n\nNoms appréciés par les utilisateurs : {', '.join(positive)}"
        if negative:
            base += f"\n\nNoms rejetés à éviter : {', '.join(negative)}"
        return base

    def build_specialized_user_prompt(
        self,
        prompt: str,
        n: int,
        langue: str,
    ) -> str:
        """Prompt utilisateur pour la génération."""
        if langue == "ar":
            return f"الوصف: {prompt}\nقم بتوليد {n} أسماء فريدة باللغة العربية."
        return f"Contexte : {prompt}\nGénère exactement {n} noms uniques en français."
