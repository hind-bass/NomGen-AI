"""
Tests pour la qualité de génération et les améliorations créativité.
Vérifie anti-doublons dataset, sampling avancé, et presets créativité.
"""
import pytest
from app.services.nomgen_core import NomGenService
from app.models.schemas import CreativityPreset


class TestDuplicateFiltering:
    """Tests de filtrage des doublons avec les datasets."""

    def setup_method(self):
        """Initialiser le service."""
        self.service = NomGenService()

    def test_training_vocab_loaded_fr(self):
        """Vocabulaire d'entraînement FR doit être chargé."""
        assert len(self.service.training_vocab_fr) > 0
        assert len(self.service.training_vocab_fr) >= 1000  # ~1451 noms FR

    def test_training_vocab_loaded_ar(self):
        """Vocabulaire d'entraînement AR doit être chargé."""
        assert len(self.service.training_vocab_ar) > 0
        assert len(self.service.training_vocab_ar) >= 500  # ~700 noms AR

    def test_duplicate_detection_fr(self):
        """Détecte les noms duplicatas français."""
        # Vérifier qu'au moins un nom du dataset est détecté
        has_training_names = len(self.service.training_vocab_fr) > 0
        if has_training_names:
            # Récupérer un nom du dataset
            training_name = next(iter(self.service.training_vocab_fr))
            assert self.service._is_duplicate_of_training(training_name, "fr")

    def test_duplicate_detection_ar(self):
        """Détecte les noms duplicatas arabes."""
        has_training_names = len(self.service.training_vocab_ar) > 0
        if has_training_names:
            training_name = next(iter(self.service.training_vocab_ar))
            assert self.service._is_duplicate_of_training(training_name, "ar")

    def test_case_insensitive_duplicate_check(self):
        """Vérification des doublons insensible à la casse."""
        # Charger un nom du dataset et le tester en majuscules
        if len(self.service.training_vocab_fr) > 0:
            training_name = next(iter(self.service.training_vocab_fr))
            assert self.service._is_duplicate_of_training(
                training_name.upper(), "fr"
            )

    def test_non_duplicate_accepted(self):
        """Les noms non-doublons doivent être acceptés."""
        # Utiliser un nom très improbable
        assert not self.service._is_duplicate_of_training(
            "xyzzzzzaaabbbccc", "fr"
        )


class TestAdvancedSampling:
    """Tests du sampling avancé avec nucleus et repetition penalty."""

    def setup_method(self):
        """Initialiser le service."""
        self.service = NomGenService()

    def test_sample_token_with_temperature(self):
        """Sampling avec temperature doit fonctionner."""
        import torch

        logits = torch.randn(1, 100)
        # Test avec différentes températures
        for temp in [0.5, 1.0, 1.5, 2.0]:
            token = self.service._sample_token(logits, temp)
            assert isinstance(token, int)
            assert 0 <= token < 100

    def test_sample_token_with_top_k(self):
        """Sampling avec top_k doit filtrer."""
        import torch

        logits = torch.randn(1, 100)
        token = self.service._sample_token(logits, 1.0, top_k=10)
        assert isinstance(token, int)
        assert 0 <= token < 100

    def test_sample_token_with_top_p(self):
        """Sampling avec top_p (nucleus) doit fonctionner."""
        import torch

        logits = torch.randn(1, 100)
        token = self.service._sample_token(logits, 1.0, top_p=0.9)
        assert isinstance(token, int)
        assert 0 <= token < 100

    def test_sample_token_with_repetition_penalty(self):
        """Sampling avec repetition penalty doit pénaliser tokens récents."""
        import torch

        logits = torch.randn(1, 100)
        recent = [0, 1, 2]  # Tokens récemment générés
        token = self.service._sample_token(
            logits, 1.0, repetition_penalty=1.2, recent_tokens=recent
        )
        assert isinstance(token, int)
        assert 0 <= token < 100

    def test_sample_token_combined_strategies(self):
        """Sampling avec combination de top_k, top_p, et repetition."""
        import torch

        logits = torch.randn(1, 100)
        token = self.service._sample_token(
            logits,
            temperature=1.1,
            top_k=25,
            top_p=0.92,
            repetition_penalty=1.1,
            recent_tokens=[5, 6, 7],
        )
        assert isinstance(token, int)
        assert 0 <= token < 100


class TestCreativityPresets:
    """Tests des presets de créativité."""

    def test_creativity_preset_enum_values(self):
        """Presets de créativité doivent avoir les bonnes valeurs."""
        assert CreativityPreset.CONSERVATEUR.value == "conservative"
        assert CreativityPreset.EQUILIBRE.value == "balanced"
        assert CreativityPreset.CREATIF.value == "creative"

    def test_generation_with_preset_conservative(self):
        """Génération avec preset conservateur doit fonctionner."""
        service = NomGenService()
        result = service.generate(
            prompt="startup tech",
            secteur="tech",
            generation_type="marque",
            langue="fr",
            n=5,
            temperature=0.8,  # Conservative
            top_k=15,
            top_p=None,
            repetition_penalty=1.0,
            seed=42,
        )
        assert len(result["noms"]) <= 5
        assert all("nom" in n for n in result["noms"])

    def test_generation_with_preset_balanced(self):
        """Génération avec preset équilibré doit fonctionner."""
        service = NomGenService()
        result = service.generate(
            prompt="marque luxe",
            secteur="luxe",
            generation_type="marque",
            langue="fr",
            n=5,
            temperature=1.1,  # Balanced
            top_k=25,
            top_p=0.92,
            repetition_penalty=1.0,
            seed=42,
        )
        assert len(result["noms"]) <= 5

    def test_generation_with_preset_creative(self):
        """Génération avec preset créatif doit fonctionner."""
        service = NomGenService()
        result = service.generate(
            prompt="startup innovative",
            secteur="general",
            generation_type="marque",
            langue="fr",
            n=5,
            temperature=1.5,  # Creative
            top_k=30,
            top_p=0.95,
            repetition_penalty=1.0,
            seed=42,
        )
        assert len(result["noms"]) <= 5

    def test_presets_generate_different_results(self):
        """Différents presets doivent générer des résultats différents."""
        service = NomGenService()

        # Générer avec conservateur
        result_conservative = service.generate(
            prompt="startup",
            secteur="tech",
            generation_type="marque",
            langue="fr",
            n=3,
            temperature=0.8,
            top_k=15,
            top_p=None,
            repetition_penalty=1.0,
            seed=42,
        )

        # Générer avec créatif
        result_creative = service.generate(
            prompt="startup",
            secteur="tech",
            generation_type="marque",
            langue="fr",
            n=3,
            temperature=1.5,
            top_k=30,
            top_p=0.95,
            repetition_penalty=1.0,
            seed=42,
        )

        # Les résultats doivent être différents (même avec même seed)
        names_conservative = {n["nom"] for n in result_conservative["noms"]}
        names_creative = {n["nom"] for n in result_creative["noms"]}

        # Au moins un nom doit être différent
        assert names_conservative != names_creative


class TestGenerationQuality:
    """Tests généraux de qualité de génération."""

    def test_generation_french_returns_valid_names(self):
        """Génération FR doit retourner des noms valides."""
        service = NomGenService()
        result = service.generate(
            prompt="marque tech",
            secteur="tech",
            generation_type="marque",
            langue="fr",
            n=5,
            temperature=1.0,
            top_k=20,
            top_p=None,
            repetition_penalty=1.0,
            seed=None,
        )
        assert len(result["noms"]) > 0
        for nom_obj in result["noms"]:
            nom = nom_obj["nom"]
            assert 3 <= len(nom) <= 15
            assert nom.isalpha()  # Que des lettres

    def test_generation_arabic_returns_valid_names(self):
        """Génération AR doit retourner des noms valides."""
        service = NomGenService()
        result = service.generate(
            prompt="شركة تقنية",
            secteur="tech",
            generation_type="marque",
            langue="ar",
            n=3,
            temperature=1.0,
            top_k=20,
            top_p=None,
            repetition_penalty=1.0,
            seed=None,
        )
        assert len(result["noms"]) > 0
        for nom_obj in result["noms"]:
            nom = nom_obj["nom"]
            assert 3 <= len(nom) <= 15

    def test_generation_reproducible_with_seed(self):
        """Génération avec seed doit être reproductible."""
        service = NomGenService()

        result1 = service.generate(
            prompt="marque",
            secteur="general",
            generation_type="marque",
            langue="fr",
            n=3,
            temperature=1.0,
            top_k=20,
            top_p=None,
            repetition_penalty=1.0,
            seed=12345,
        )

        result2 = service.generate(
            prompt="marque",
            secteur="general",
            generation_type="marque",
            langue="fr",
            n=3,
            temperature=1.0,
            top_k=20,
            top_p=None,
            repetition_penalty=1.0,
            seed=12345,
        )

        names1 = [n["nom"] for n in result1["noms"]]
        names2 = [n["nom"] for n in result2["noms"]]
        assert names1 == names2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
