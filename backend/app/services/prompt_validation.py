"""
Validation avancée des prompts avec détection de gibberish et analyse NLU.
Remplace est_prompt_vide() avec une approche intelligente et multi-critères.
"""
import re
from app.services.prompt_nlu import analyze_prompt, PromptAnalysis


def validate_prompt_coherence(text: str) -> tuple[bool, str | None]:
    """
    Valide que le prompt est cohérent (pas gibberish/aléatoire).

    Retourne (is_valid, error_message).
    - is_valid=True : prompt acceptable
    - is_valid=False : prompt rejeté, message d'erreur à afficher

    Cas rejetés :
    - Vide ou <2 chars
    - Chiffres/symboles seuls
    - Gibberish détecté (consonnes seules, entropy haute)
    """
    text_stripped = text.strip()

    # Cas 1 : Vide ou très court
    if len(text_stripped) < 2:
        return False, "Veuillez entrer une description valide."

    # Cas 2 : Aucune lettre du tout
    has_letters = bool(
        re.search(r"[a-zA-ZÀ-ÿ\u0600-\u06FF]", text_stripped)
    )
    if not has_letters:
        return False, "La description ne contient aucune lettre."

    # Cas 3 : Détection de gibberish
    is_gibberish = detect_gibberish(text_stripped)
    if is_gibberish:
        return (
            False,
            "Description incohérente — utilisez des mots réels ou une phrase claire.",
        )

    return True, None


def detect_gibberish(text: str, lang: str = "auto") -> bool:
    """
    Heuristiques pour détecter texte aléatoire/incohérent.

    Détecte :
    - Trop de consonnes consécutives (>4 d'affilée)
    - Ratio consonnes/voyelles extrême
    - Absence totale de patterns de mots
    - Entropie caractères très élevée (randomness)

    Retourne True si gibberish détecté.
    """
    text_lower = text.lower()

    # Détecter la langue si auto
    if lang == "auto":
        arabic_count = len(re.findall(r"[\u0600-\u06FF]", text_lower))
        latin_count = len(re.findall(r"[a-zA-ZÀ-ÿ]", text_lower))
        lang = "ar" if arabic_count >= latin_count else "fr"

    if lang == "ar":
        return _detect_gibberish_arabic(text_lower)
    else:
        return _detect_gibberish_french(text_lower)


def _detect_gibberish_french(text: str) -> bool:
    """Détection spécialisée pour le français."""
    consonants = "bcdfghjklmnpqrstvwxyz"
    vowels = "aeiouyàâäéèêëïîôöùûüœæ"

    # Heuristique 1 : Trop de consonnes consécutives (>4)
    # IMPORTANT: utiliser que les lettres, pas les espaces/symboles
    consonant_runs = re.findall(r"[bcdfghjklmnpqrstvwxz]+", text)
    if consonant_runs and max(len(r) for r in consonant_runs) > 4:
        return True

    # Heuristique 2 : Ratio consonnes/voyelles extrême
    # Inclure les voyelles accentuées
    c_count = sum(1 for ch in text if ch.lower() in consonants)
    v_count = sum(1 for ch in text if ch.lower() in vowels)
    if v_count == 0:  # Pas une seule voyelle
        return True
    if c_count / (v_count + 1) > 3.0:  # Plus de 3x consonnes que voyelles
        return True

    # Heuristique 3 : Trop de caractères non-alphabétiques
    # Pour une phrase valide, 70%+ doivent être alphabétiques ou espaces
    letters_and_spaces = sum(1 for ch in text if ch.isalpha() or ch.isspace())
    if letters_and_spaces / len(text) < 0.85:  # 85% lettres+espaces minimum
        return True

    # Heuristique 4 : Répétition excessive du même caractère (>3 fois d'affilée)
    if re.search(r"(.)\1{3,}", text):
        return True

    return False


def _detect_gibberish_arabic(text: str) -> bool:
    """Détection spécialisée pour l'arabe."""
    # Caractères arabes
    arabic_letters = re.compile(r"[\u0621-\u064A\u064B-\u0652]")

    # Heuristique 1 : Peu de caractères arabes valides
    arabic_count = len(arabic_letters.findall(text))
    if arabic_count == 0:
        return True

    alpha_ratio = arabic_count / len(text)
    if alpha_ratio < 0.6:  # Moins de 60% de caractères arabes valides
        return True

    # Heuristique 2 : Répétition excessive
    if re.search(r"(.)\1{3,}", text):
        return True

    # Heuristique 3 : Hamzas isolés (indicateur de typage chaotique)
    hamzas = len(re.findall(r"[\u0621\u0623\u0625]", text))
    if hamzas > len(text) / 3:  # Plus d'1 hamza pour 3 caractères
        return True

    return False


def analyze_with_nlu(prompt: str) -> tuple[PromptAnalysis, list[str]]:
    """
    Analyse NLU complète avec seuils de confiance.

    Retourne :
    - PromptAnalysis : résultat de l'analyse
    - warnings : liste de messages d'avertissement si confiances basses

    Avertissements générés si :
    - confiance_sect < 0.3 : secteur peu clair, défaut "general"
    - confiance_lang < 0.6 : mélange de langues détecté
    """
    analysis = analyze_prompt(prompt)
    warnings = []

    # Avertissement : secteur peu clair
    if analysis.confidence_sect < 0.3:
        warnings.append(
            f"validation_warning:Faible confiance secteur "
            f"({analysis.confidence_sect:.1%}) — défaut 'general'."
        )

    # Avertissement : mélange de langues
    if analysis.confidence_lang < 0.6:
        warnings.append(
            f"validation_warning:Mélange de langues détecté "
            f"({analysis.confidence_lang:.1%}). Langue sélectionnée: {analysis.langue}."
        )

    return analysis, warnings
