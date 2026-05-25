"""
Tests pour la validation intelligente des prompts.
Vérifie gibberish detection, seuils NLU, et messages d'erreur clairs.
"""
import pytest
from app.services.prompt_validation import (
    validate_prompt_coherence,
    detect_gibberish,
    analyze_with_nlu,
)


class TestValidatePromptCoherence:
    """Tests de validation de cohérence des prompts."""

    def test_empty_prompt_rejected(self):
        """Prompt vide doit être rejeté."""
        is_valid, msg = validate_prompt_coherence("")
        assert not is_valid
        assert "valide" in msg.lower()

    def test_single_char_rejected(self):
        """Prompt d'un seul caractère doit être rejeté."""
        is_valid, msg = validate_prompt_coherence("a")
        assert not is_valid

    def test_numbers_only_rejected(self):
        """Prompt avec chiffres seuls doit être rejeté."""
        is_valid, msg = validate_prompt_coherence("12345")
        assert not is_valid
        assert "lettre" in msg.lower()

    def test_symbols_only_rejected(self):
        """Prompt avec symboles seuls doit être rejeté."""
        is_valid, msg = validate_prompt_coherence("!@#$%^&*()")
        assert not is_valid
        assert "lettre" in msg.lower()

    def test_gibberish_french_rejected(self):
        """Gibberish français doit être rejeté."""
        is_valid, msg = validate_prompt_coherence("jdhfkjhdfkjhdfkjh")
        assert not is_valid
        assert "incohérent" in msg.lower()

    def test_gibberish_with_no_vowels_rejected(self):
        """Texte sans voyelles doit être rejeté."""
        is_valid, msg = validate_prompt_coherence("bcdfghjklmnpqrstvwxyz")
        assert not is_valid

    def test_normal_french_accepted(self):
        """Prompt français normal doit être accepté."""
        is_valid, msg = validate_prompt_coherence("startup tech innovante")
        assert is_valid
        assert msg is None

    def test_short_but_valid_accepted(self):
        """Prompt court mais valide (ex: "bio") doit être accepté."""
        is_valid, msg = validate_prompt_coherence("bio")
        assert is_valid
        assert msg is None

    def test_arabic_prompt_accepted(self):
        """Prompt arabe valide doit être accepté."""
        is_valid, msg = validate_prompt_coherence("شركة تقنية")
        assert is_valid
        assert msg is None

    def test_mixed_language_accepted(self):
        """Prompt mélangé FR/AR doit être accepté."""
        is_valid, msg = validate_prompt_coherence("marque فاخر")
        assert is_valid
        assert msg is None


class TestDetectGibberish:
    """Tests de détection de gibberish."""

    def test_gibberish_french_consonant_heavy(self):
        """Gibberish français avec trop de consonnes."""
        assert detect_gibberish("jdhfkjhdfkjh", "fr")

    def test_gibberish_french_no_vowels(self):
        """Gibberish français sans voyelles."""
        assert detect_gibberish("bcdfghjklmnp", "fr")

    def test_gibberish_french_extreme_ratio(self):
        """Gibberish avec ratio consonnes/voyelles extrême."""
        assert detect_gibberish("bbbbbcccccdddd", "fr")

    def test_gibberish_repetition(self):
        """Gibberish avec répétition excessive."""
        assert detect_gibberish("aaaaaabbbb", "fr")

    def test_valid_french_not_gibberish(self):
        """Texte français valide ne doit pas être gibberish."""
        assert not detect_gibberish("bonjour", "fr")
        assert not detect_gibberish("technologie", "fr")
        assert not detect_gibberish("startup", "fr")

    def test_short_valid_word_not_gibberish(self):
        """Mot court valide ne doit pas être gibberish."""
        assert not detect_gibberish("bio", "fr")
        assert not detect_gibberish("spa", "fr")

    def test_arabic_gibberish_detection(self):
        """Détection de gibberish arabe."""
        # Trop de hamzas
        assert detect_gibberish("ؤؤؤؤؤؤؤ", "ar")

    def test_arabic_valid_not_gibberish(self):
        """Texte arabe valide ne doit pas être gibberish."""
        assert not detect_gibberish("شركة", "ar")
        assert not detect_gibberish("تقنية", "ar")

    def test_auto_detect_french(self):
        """Auto-détection de langue française."""
        assert not detect_gibberish("bonjour", "auto")

    def test_auto_detect_arabic(self):
        """Auto-détection de langue arabe."""
        assert not detect_gibberish("شركة", "auto")


class TestAnalyzeWithNLU:
    """Tests d'analyse NLU avec seuils de confiance."""

    def test_clear_french_tech_prompt(self):
        """Prompt clair français tech."""
        analysis, warnings = analyze_with_nlu("startup tech innovante")
        assert analysis.langue == "fr"
        assert analysis.secteur == "tech"
        assert analysis.confidence_sect > 0.3
        assert len(warnings) == 0  # Pas d'avertissements si confiance OK

    def test_clear_arabic_prompt(self):
        """Prompt clair arabe."""
        analysis, warnings = analyze_with_nlu("شركة تقنية")
        assert analysis.langue == "ar"
        assert analysis.confidence_lang >= 0.5
        assert len(warnings) == 0

    def test_low_sector_confidence_warning(self):
        """Prompt avec confiance secteur basse génère warning."""
        analysis, warnings = analyze_with_nlu("xyz")
        assert analysis.confidence_sect < 0.3
        assert any("validation_warning" in w for w in warnings)
        assert any("confiance secteur" in w.lower() for w in warnings)

    def test_mixed_language_warning(self):
        """Mélange de langues génère warning."""
        analysis, warnings = analyze_with_nlu("marque فاخر")
        assert analysis.confidence_lang < 0.6
        assert any("validation_warning" in w for w in warnings)
        assert any("langue" in w.lower() for w in warnings)

    def test_luxury_sector_detected(self):
        """Secteur luxe détecté."""
        analysis, warnings = analyze_with_nlu("marque luxe premium")
        assert analysis.secteur == "luxe"

    def test_food_sector_detected(self):
        """Secteur food détecté."""
        analysis, warnings = analyze_with_nlu("restaurant gastronomie")
        assert analysis.secteur == "food"

    def test_arabic_keywords_work(self):
        """Mots-clés arabes détectés correctement."""
        analysis, warnings = analyze_with_nlu("شركة تقنية")
        assert analysis.secteur == "tech"

    def test_marque_type_detected(self):
        """Type "marque" détecté."""
        analysis, warnings = analyze_with_nlu("marque luxe")
        assert analysis.generation_type == "marque"

    def test_societe_type_detected(self):
        """Type "société" détecté."""
        analysis, warnings = analyze_with_nlu("société de services")
        assert analysis.generation_type == "societe"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
