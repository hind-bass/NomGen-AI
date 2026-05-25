"""
Test manual du router FastAPI avec validation et génération améliorées.
"""
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=== TEST API: Endpoint /api/generate ===\n")

# Test 1: Prompt vide
print("TEST 1: POST /api/generate avec prompt vide")
response = client.post("/api/generate", json={
    "prompt": "",
    "langue": "fr",
    "n": 5
})
print(f"  Status: {response.status_code}")
data = response.json()
print(f"  Noms: {len(data['noms'])}")
print(f"  Tokens: {data['tokens_detectes']}")
assert len(data['noms']) == 0
assert any("validation_error" in t for t in data['tokens_detectes'])

# Test 2: Prompt gibberish
print("\nTEST 2: POST /api/generate avec prompt gibberish")
response = client.post("/api/generate", json={
    "prompt": "jdhfkjhdfkjhdfkjh",
    "langue": "fr",
    "n": 5
})
print(f"  Status: {response.status_code}")
data = response.json()
print(f"  Noms: {len(data['noms'])}")
print(f"  Tokens: {data['tokens_detectes']}")
assert len(data['noms']) == 0
assert any("validation_error" in t for t in data['tokens_detectes'])

# Test 3: Prompt valide avec preset équilibré
print("\nTEST 3: POST /api/generate avec prompt valide + preset EQUILIBRE")
response = client.post("/api/generate", json={
    "prompt": "startup tech",
    "langue": "fr",
    "creativity_preset": "balanced",
    "n": 3
})
print(f"  Status: {response.status_code}")
data = response.json()
print(f"  Noms générés ({len(data['noms'])}):")
for nom_obj in data['noms']:
    print(f"    - {nom_obj['nom']} (score: {nom_obj['score']:.0f})")
print(f"  Strategy: {data['tokens_detectes'][0]}")
assert len(data['noms']) <= 3
assert all("nom" in n for n in data['noms'])

# Test 4: Prompt valide avec preset créatif et top_p
print("\nTEST 4: POST /api/generate avec preset CREATIF + top_p")
response = client.post("/api/generate", json={
    "prompt": "marque luxe",
    "langue": "fr",
    "creativity_preset": "creative",
    "top_p": 0.95,
    "repetition_penalty": 1.2,
    "n": 2
})
print(f"  Status: {response.status_code}")
data = response.json()
print(f"  Noms générés ({len(data['noms'])}):")
for nom_obj in data['noms']:
    print(f"    - {nom_obj['nom']}")
assert len(data['noms']) <= 2

# Test 5: Override presets avec temperature explicite
print("\nTEST 5: POST /api/generate avec override temperature")
response = client.post("/api/generate", json={
    "prompt": "restaurant",
    "langue": "fr",
    "creativity_preset": "balanced",
    "temperature": 0.5,  # Override le preset
    "n": 2
})
print(f"  Status: {response.status_code}")
data = response.json()
print(f"  Noms générés: {len(data['noms'])}")
assert response.status_code == 200

# Test 6: POST /api/analyze-prompt
print("\nTEST 6: POST /api/analyze-prompt")
response = client.post("/api/analyze-prompt", json={
    "prompt": "startup tech innovante"
})
print(f"  Status: {response.status_code}")
data = response.json()
print(f"  Langue: {data['langue']}")
print(f"  Secteur: {data['secteur']}")
print(f"  Type: {data['generation_type']}")
print(f"  Confiances: lang={data['confidence_lang']}, sect={data['confidence_sect']}")
print(f"  Keywords: {data['keywords_found']}")
assert response.status_code == 200
assert data['langue'] in ['fr', 'ar']

print("\n=== TOUS LES TESTS API RÉUSSIS ===")
