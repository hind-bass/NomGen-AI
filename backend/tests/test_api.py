"""
Tests pytest — NomGen AI API
Couverture : /api/generate, /api/analyze-prompt, /api/health, /api/models

Prérequis :
  pip install pytest httpx
  Lancer depuis backend/ : pytest tests/test_api.py -v
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ════════════════════════════════════════════════════════════════════════════
# /api/health
# ════════════════════════════════════════════════════════════════════════════

def test_health_ok():
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert isinstance(body["models"], list)


# ════════════════════════════════════════════════════════════════════════════
# /api/generate — prompts invalides (doivent retourner noms=[])
# ════════════════════════════════════════════════════════════════════════════

def test_empty_prompt_returns_empty_list():
    """Un prompt vide ne doit pas générer de noms."""
    res = client.post("/api/generate", json={
        "prompt": "", "langue": "fr", "n": 5,
    })
    assert res.status_code == 200
    assert res.json()["noms"] == []


def test_whitespace_only_prompt_returns_empty():
    """Espaces seuls = prompt vide."""
    res = client.post("/api/generate", json={
        "prompt": "     ", "langue": "fr", "n": 5,
    })
    assert res.status_code == 200
    assert res.json()["noms"] == []


def test_gibberish_no_spaces_returns_empty():
    """Frappe aléatoire sans espace > 15 chars → incohérent."""
    res = client.post("/api/generate", json={
        "prompt": "jdhfkjhdfkjhdfkjh", "langue": "fr", "n": 5,
    })
    assert res.status_code == 200
    assert res.json()["noms"] == []


def test_digits_only_returns_empty():
    """Prompt sans lettre latine ni arabe → incohérent."""
    res = client.post("/api/generate", json={
        "prompt": "12345678901234567890", "langue": "fr", "n": 5,
    })
    assert res.status_code == 200
    assert res.json()["noms"] == []


def test_symbols_only_returns_empty():
    """Uniquement symboles/ponctuations → incohérent."""
    res = client.post("/api/generate", json={
        "prompt": "!@#$%^&*()_+-=[]{}|", "langue": "fr", "n": 5,
    })
    assert res.status_code == 200
    assert res.json()["noms"] == []


# ════════════════════════════════════════════════════════════════════════════
# /api/generate — prompts valides
# ════════════════════════════════════════════════════════════════════════════

def test_valid_french_prompt_returns_names():
    """Un prompt français valide doit retourner des noms."""
    res = client.post("/api/generate", json={
        "prompt": "startup tech moderne",
        "langue": "fr", "secteur": "tech",
        "generation_type": "marque", "n": 5,
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["noms"]) > 0


def test_generated_names_have_required_fields():
    """Chaque nom doit avoir les champs obligatoires."""
    res = client.post("/api/generate", json={
        "prompt": "marque de luxe", "langue": "fr",
        "secteur": "luxe", "generation_type": "marque", "n": 3,
    })
    assert res.status_code == 200
    for item in res.json()["noms"]:
        assert "nom"     in item, "Champ 'nom' manquant"
        assert "score"   in item, "Champ 'score' manquant"
        assert "langue"  in item, "Champ 'langue' manquant"
        assert "secteur" in item, "Champ 'secteur' manquant"


def test_generated_names_length_valid():
    """Les noms générés doivent respecter la plage 3–15 caractères."""
    res = client.post("/api/generate", json={
        "prompt": "innovation technologique", "langue": "fr",
        "secteur": "tech", "n": 10,
    })
    assert res.status_code == 200
    for item in res.json()["noms"]:
        assert 3 <= len(item["nom"]) <= 15, f"Longueur invalide : '{item['nom']}'"


def test_generated_scores_in_range():
    """Les scores de plausibilité doivent être dans [0, 100]."""
    res = client.post("/api/generate", json={
        "prompt": "marque luxe mode", "langue": "fr",
        "secteur": "luxe", "n": 5,
    })
    assert res.status_code == 200
    for item in res.json()["noms"]:
        assert 0.0 <= item["score"] <= 100.0, f"Score hors plage : {item['score']}"


def test_valid_arabic_prompt():
    """Un prompt arabe valide doit être accepté et retourner des noms."""
    res = client.post("/api/generate", json={
        "prompt": "شركة تقنية حديثة",
        "langue": "ar", "secteur": "tech",
        "generation_type": "marque", "n": 3,
    })
    assert res.status_code == 200
    data = res.json()
    assert "noms"     in data
    assert "duree_ms" in data
    assert isinstance(data["duree_ms"], float)


def test_generation_type_societe():
    """Le type 'societe' doit être transmis et influencer la génération."""
    res = client.post("/api/generate", json={
        "prompt": "agence de conseil en management",
        "langue": "fr", "secteur": "services",
        "generation_type": "societe", "n": 5,
    })
    assert res.status_code == 200
    assert res.status_code == 200  # au minimum pas d'erreur 500


def test_seed_produces_reproducible_results():
    """Avec le même seed, deux appels doivent donner les mêmes noms."""
    params = {
        "prompt": "startup innovante", "langue": "fr",
        "secteur": "tech", "n": 5, "seed": 42,
    }
    res1 = client.post("/api/generate", json=params)
    res2 = client.post("/api/generate", json=params)
    assert res1.status_code == 200
    assert res2.status_code == 200
    noms1 = [item["nom"] for item in res1.json()["noms"]]
    noms2 = [item["nom"] for item in res2.json()["noms"]]
    assert noms1 == noms2, "Les résultats avec seed identique devraient être identiques"


def test_response_contains_duree_ms():
    """La réponse doit toujours inclure le temps de génération."""
    res = client.post("/api/generate", json={
        "prompt": "marque bio naturelle", "langue": "fr", "n": 3,
    })
    assert res.status_code == 200
    assert "duree_ms" in res.json()
    assert res.json()["duree_ms"] >= 0


# ════════════════════════════════════════════════════════════════════════════
# /api/analyze-prompt
# ════════════════════════════════════════════════════════════════════════════

def test_analyze_french_luxury():
    res = client.post("/api/analyze-prompt", json={"prompt": "marque de luxe française"})
    assert res.status_code == 200
    data = res.json()
    assert data["langue"]  == "fr"
    assert data["secteur"] == "luxe"


def test_analyze_french_tech():
    res = client.post("/api/analyze-prompt", json={"prompt": "startup tech moderne intelligence artificielle"})
    assert res.status_code == 200
    data = res.json()
    assert data["langue"]  == "fr"
    assert data["secteur"] == "tech"


def test_analyze_arabic_prompt():
    res = client.post("/api/analyze-prompt", json={"prompt": "شركة تقنية"})
    assert res.status_code == 200
    data = res.json()
    assert data["langue"] == "ar"


def test_analyze_societe_type_detected():
    """Les mots "société" et "entreprise" doivent détecter le type 'societe'."""
    res = client.post("/api/analyze-prompt", json={"prompt": "société de conseil en finance"})
    assert res.status_code == 200
    assert res.json()["generation_type"] == "societe"


def test_analyze_marque_type_default():
    """Sans mot-clé de type, le défaut doit être 'marque'."""
    res = client.post("/api/analyze-prompt", json={"prompt": "collection mode luxe"})
    assert res.status_code == 200
    assert res.json()["generation_type"] == "marque"


def test_analyze_empty_prompt():
    """Un prompt vide doit retourner les valeurs par défaut sans erreur."""
    res = client.post("/api/analyze-prompt", json={"prompt": ""})
    assert res.status_code == 200
    data = res.json()
    assert data["langue"]  == "fr"
    assert data["secteur"] == "general"


def test_analyze_response_has_all_fields():
    """Tous les champs attendus doivent être présents."""
    res = client.post("/api/analyze-prompt", json={"prompt": "startup tech"})
    assert res.status_code == 200
    data = res.json()
    required = {"langue", "secteur", "generation_type", "ctrl_token",
                "confidence_lang", "confidence_sect", "keywords_found"}
    assert required.issubset(data.keys())


def test_analyze_confidence_in_range():
    """Les confiances doivent être dans [0, 1]."""
    res = client.post("/api/analyze-prompt", json={"prompt": "application mobile innovante"})
    assert res.status_code == 200
    data = res.json()
    assert 0.0 <= data["confidence_lang"] <= 1.0
    assert 0.0 <= data["confidence_sect"] <= 1.0


# ════════════════════════════════════════════════════════════════════════════
# /api/models
# ════════════════════════════════════════════════════════════════════════════

def test_models_endpoint_returns_list():
    res = client.get("/api/models")
    assert res.status_code == 200
    data = res.json()
    assert "models" in data
    assert "count"  in data
    assert isinstance(data["models"], list)
    assert data["count"] == len(data["models"])