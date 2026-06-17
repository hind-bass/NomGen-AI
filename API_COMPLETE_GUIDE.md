# 📚 API NomGen AI - Guide Complet

## Vue d'Ensemble

```
┌──────────────────────────────────────────────────────────┐
│          NOMGEN AI - Architecture API                    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Mode A (Automatique)  │  Mode B (Intelligent)          │
│  ─────────────────────┼─────────────────────            │
│  POST /api/generate   │  POST /api/generate-llm-simple  │
│  (nanoGPT local)      │  (Ollama/OpenAI)               │
│  ✨ Rapide (100ms)    │  🤖 Intelligent (5-30s)        │
│  💰 Gratuit           │  💵 API payante                │
│  🏠 100% local        │  🌐 Réseau requis              │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Mode A: Génération Automatique (nanoGPT Local)

### 📌 Endpoint
```
POST /api/generate
Content-Type: application/json
Authorization: Bearer {token}  [OPTIONNEL - aucune si anonyme]
```

### 📋 Body Parameters

```json
{
  "secteur": "LUXE",              // Catégorie: TECH, FOOD, LUXE, GENERAL, etc.
  "langue": "fr",                 // Langue: "fr" ou "ar"
  "n": 10,                        // Nombre de noms (1-50)
  "temperature": 1.0,             // Créativité (0.1-2.5)
  "top_k": 20,                    // Top-K sampling (1-100)
  "seed": null,                   // Reproducibilité (null = aléatoire)
  "prompt": ""                    // OPTIONNEL - ignoré si fourni
}
```

### ✅ Response

```json
{
  "noms": [
    {
      "nom": "luxora",
      "score": 85.3,
      "langue": "fr",
      "secteur": "LUXE"
    },
    {
      "nom": "syntaxo",
      "score": 82.1,
      "langue": "fr",
      "secteur": "LUXE"
    }
  ],
  "tokens_detectes": ["luxe", "marque"],
  "duree_ms": 87.5
}
```

### 🔗 Exemples Curl

**Français - Secteur Luxe:**
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "secteur": "LUXE",
    "langue": "fr",
    "n": 10,
    "temperature": 1.0
  }'
```

**Arabe - Secteur Technologie:**
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "secteur": "TECH",
    "langue": "ar",
    "n": 8,
    "temperature": 0.8
  }'
```

### 📊 Paramètres Détaillés

| Param | Type | Range | Défaut | Notes |
|-------|------|-------|--------|-------|
| `secteur` | string | TECH, FOOD, LUXE, GENERAL, SANTE, FINANCE | GENERAL | Utilise modèle spécialisé si disponible |
| `langue` | string | "fr", "ar", "en" | "fr" | Sélectionne le vocabulaire |
| `n` | integer | 1-50 | 10 | Nombre de suggestions |
| `temperature` | float | 0.1-2.5 | 1.0 | 0.1=déterministe, 2.5=créatif |
| `top_k` | integer | 1-100 | 20 | Diversité: 1=déterministe, 100=maximum |
| `seed` | integer/null | any | null | Seed pour reproducibilité |

---

## Mode B: Génération Intelligente (LLM + Prompt)

### 📌 Endpoint
```
POST /api/generate-llm-simple
Content-Type: application/json
Authorization: Bearer {token}  [OPTIONNEL]
```

### 📋 Body Parameters

```json
{
  "prompt": "Marque de luxe française pour cosmétiques haut de gamme",
  "langue": "fr",                 // "fr", "ar", "en"
  "model": "mistral",             // Voir /api/models/recommended
  "secteur": "LUXE",              // OPTIONNEL - métadonnées
  "type_nom": "marque",           // OPTIONNEL - métadonnées
  "n": 10,                        // Nombre (1-20)
  "temperature": 0.7              // Pour LLM (0.1-1.5)
}
```

### ✅ Response

```json
{
  "noms": [
    {
      "nom": "essence botanique",
      "score": 88.0,
      "langue": "fr",
      "secteur": "LUXE",
      "source": "llm"
    },
    {
      "nom": "eclair naturel",
      "score": 85.0,
      "langue": "fr",
      "secteur": "LUXE",
      "source": "llm"
    }
  ],
  "model_used": "mistral",
  "duree_ms": 18750.3
}
```

### 🔗 Exemples Curl

**Français - Mistral (Ollama):**
```bash
curl -X POST http://localhost:8000/api/generate-llm-simple \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Application mobile pour apprendre le français. Cible: enfants 5-12 ans. Ludique, interactif, educatif",
    "langue": "fr",
    "model": "mistral",
    "secteur": "TECH",
    "n": 10
  }'
```

**Arabe - Allam (Modèle Arabe Spécialisé):**
```bash
curl -X POST http://localhost:8000/api/generate-llm-simple \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "تطبيق تعليمي للأطفال العرب. يعلم اللغة العربية والرياضيات. تفاعلي وممتع",
    "langue": "ar",
    "model": "allam",
    "secteur": "TECH",
    "n": 10
  }'
```

**Français - OpenAI Fallback:**
```bash
# Nécessite OPENAI_API_KEY
export OPENAI_API_KEY="sk-..."

curl -X POST http://localhost:8000/api/generate-llm-simple \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Startup fintech, paiements digitaux, cible jeunes adultes",
    "langue": "fr",
    "model": "gpt-3.5-turbo",  # Sera utilisé si Ollama offline
    "n": 10
  }'
```

### 📊 Modèles Recommandés

**GET /api/models/recommended**

```bash
# Tous les modèles
curl http://localhost:8000/api/models/recommended

# Français seulement
curl http://localhost:8000/api/models/recommended?langue=fr

# Arabe seulement
curl http://localhost:8000/api/models/recommended?langue=ar
```

**Response:**
```json
{
  "fr": ["mistral", "dolphin-mixtral", "neural-chat"],
  "ar": ["allam", "fanar", "acegpt"],
  "en": ["mistral", "neural-chat"]
}
```

### 📊 Modèles Supportés

#### Français
| Modèle | Provider | Setup | Perf | Cost |
|--------|----------|-------|------|------|
| mistral | Ollama | `ollama pull mistral` | ⚡ Bon | Gratuit |
| gpt-4o | OpenAI | API Key | ⚡⚡ Excellent | $$ |
| gpt-3.5-turbo | OpenAI | API Key | ⚡ Bon | $ |
| deepseek | Ollama | `ollama pull deepseek` | ⚡⚡ Très bon | Gratuit |

#### Arabe
| Modèle | Provider | Setup | Spécialité |
|--------|----------|-------|-----------|
| allam | SDAIA | Via API | **MEILLEUR pour Arabe** |
| fanar | Qatar | Via API | Arabe classique |
| acegpt | Local | Ollama | Arabe/Anglais |
| jais | MBZUAI | Via API | Arabe formel |

---

## 🔄 Historique & Analytics

### 1️⃣ Voir l'Historique
```bash
GET /api/history
Authorization: Bearer {token}
```

**Response:**
```json
[
  {
    "id": 1,
    "prompt": "Luxe innovation",
    "langue": "fr",
    "secteur": "LUXE",
    "n_generated": 10,
    "mode": "A",
    "created_at": "2024-06-16T12:00:00"
  },
  {
    "id": 2,
    "prompt": "Application mobile éducative",
    "langue": "fr",
    "secteur": "TECH",
    "n_generated": 8,
    "mode": "B",
    "created_at": "2024-06-16T12:15:00"
  }
]
```

### 2️⃣ Ajouter aux Favoris
```bash
POST /api/favorites
Authorization: Bearer {token}
Content-Type: application/json

{
  "nom": "luxora",
  "score": 85.3,
  "langue": "fr",
  "secteur": "LUXE"
}
```

### 3️⃣ Récupérer Favoris
```bash
GET /api/favorites
Authorization: Bearer {token}
```

---

## 🔐 Authentification

### Créer Compte
```bash
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

### Se Connecter
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "role": "user",
  "email": "user@example.com"
}
```

### Utiliser Token
```bash
curl http://localhost:8000/api/generate \
  -H "Authorization: Bearer eyJhbGc..."
```

---

## 🚀 Setup Complet

### 1. Mode A (toujours disponible)
```bash
cd backend
python -m uvicorn app.main:app --reload
```

### 2. Mode B - Option A: Ollama Local
```bash
# Terminal 1: Ollama
ollama serve

# Terminal 2: Télécharger modèles
ollama pull mistral          # Français
ollama pull allam            # Arabe (si disponible)

# Terminal 3: Backend
python -m uvicorn app.main:app --reload
```

### 3. Mode B - Option B: OpenAI
```bash
# Variables d'env
export OPENAI_API_KEY="sk-..."

# Backend (fallback auto)
python -m uvicorn app.main:app --reload
```

---

## 📈 Performances & Benchmarks

| Mode | Model | Langue | Temps | Qualité | Coût |
|------|-------|--------|-------|---------|------|
| A | nanoGPT | FR | 87ms | ⭐⭐⭐ | Gratuit |
| A | nanoGPT | AR | 92ms | ⭐⭐⭐ | Gratuit |
| B | Mistral | FR | 18.5s | ⭐⭐⭐⭐ | Gratuit |
| B | GPT-4o | FR | 12.3s | ⭐⭐⭐⭐⭐ | $$ |
| B | Allam | AR | 15.2s | ⭐⭐⭐⭐⭐ | $$ |

---

## ❌ Codes d'Erreur

| Code | Message | Cause |
|------|---------|-------|
| 400 | Invalid request | Paramètres manquants/invalides |
| 401 | Token invalide | Token expiré ou incorrect |
| 403 | Accès refusé | Admin requis |
| 404 | Ressource introuvable | ID invalide |
| 422 | Validation error | Format de données invalide |
| 503 | Service unavailable | Ollama/API hors ligne |
| 502 | Bad gateway | Erreur LLM/API externe |

---

## 💡 Conseils d'Optimisation

### Mode A
- ✅ Utilisez `seed` pour tests reproductibles
- ✅ Ajustez `temperature` (1.0 = équilibré)
- ✅ Batch de 100+ générations en parallèle

### Mode B
- ✅ Prompt détaillé = meilleur résultat
- ✅ Utilisez `temperature: 0.7` pour équilibre
- ✅ Ollama local > OpenAI pour coût/latence
- ✅ Allam meilleur pour Arabe

---

## 🔗 Endpoint Racine
```bash
GET http://localhost:8000/
```

Retourne la liste complète des endpoints disponibles.
