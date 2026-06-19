# 🎯 Deux Modes de Génération NomGen AI

## Mode A: Génération Automatique (Local nanoGPT)

### Concept
- **Sans prompt requis**
- User choisit: `type` + `categorie` + `langue`
- Système génère via modèle entraîné localement
- **Rapide** (~100ms), **Privé**, **Gratuit**

### Paramètres
```json
{
  "type_nom": "marque" | "societe",
  "secteur": "LUXE" | "TECH" | "FOOD" | "GENERAL" | ...,
  "langue": "fr" | "ar" | "en",
  "n": 10,
  "temperature": 1.0,
  "top_k": 20,
  "seed": null
}
```

### Hiérarchie Modèles
```
1. model_{langue}_{secteur}.pt    (Spécialisé)
   ↓ fallback
2. model_{langue}.pt              (Générique)
```

### Exemples Utilisation

**curl:**
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "secteur": "TECH",
    "langue": "fr",
    "n": 10,
    "temperature": 1.0
  }'
```

**Response:**
```json
{
  "noms": [
    {
      "nom": "syntaxo",
      "score": 85.3,
      "langue": "fr",
      "secteur": "TECH"
    },
    ...
  ],
  "tokens_detectes": ["tech", "innovation"],
  "duree_ms": 87.5
}
```

---

## Mode B: Génération Intelligente (LLM + Prompt)

### Concept
- **Prompt requis** (description produit/idée)
- User décrit librement son projet
- Modèle LLM sélectionné selon la langue
- **Moins rapide** (~5-30s), **Nécessite API**, **Intelligente**

### Paramètres
```json
{
  "prompt": "Marque de luxe française pour le secteur cosmétique...",
  "langue": "fr" | "ar",
  "model": "mistral" | "gpt-4o" | "allam" | ...,
  "secteur": "LUXE",
  "type_nom": "marque",
  "n": 10,
  "temperature": 0.7
}
```

### Modèles Recommandés par Langue

#### 🇫🇷 Français
| Modèle | Provider | Latency | Coût | Recommendation |
|--------|----------|---------|------|-----------------|
| GPT-4o | OpenAI | 10-20s | $$ | ⭐⭐⭐ Meilleur |
| Mistral | Ollama (local) | 15-30s | Free | ⭐⭐⭐ Recommandé |
| DeepSeek | Ollama | 20-40s | Free | ⭐⭐ Bon |
| Claude | Anthropic | 10-20s | $$ | ⭐⭐⭐ Très bon |

#### 🇸🇦 Arabe
| Modèle | Provider | Latency | Spécialité | Recommendation |
|--------|----------|---------|-----------|-----------------|
| Allam | SDAIA | 15-30s | **Arabe NLP** | ⭐⭐⭐⭐ MEILLEUR |
| Fanar | Qatar | 20-40s | Arabe classique | ⭐⭐⭐ Très bon |
| AceGPT | Local | 25-45s | Arabe/Anglais | ⭐⭐ Bon |
| Jais | MBZUAI | 15-30s | Arabe formel | ⭐⭐⭐ Bon |

### Exemples Utilisation

**curl Français (Mistral):**
```bash
curl -X POST http://localhost:8000/api/generate-llm-simple \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Marque de cosmétiques haut de gamme, luxe naturel, produits bio, cible femmes 25-45 ans",
    "langue": "fr",
    "model": "mistral",
    "secteur": "LUXE",
    "n": 10
  }'
```

**curl Arabe (Allam):**
```bash
curl -X POST http://localhost:8000/api/generate-llm-simple \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "تطبيق تعليمي للأطفال العرب، تفاعلي، ممتع، يعلم اللغة العربية والرياضيات",
    "langue": "ar",
    "model": "allam",
    "secteur": "TECH",
    "n": 10
  }'
```

**Response:**
```json
{
  "noms": [
    {
      "nom": "syntaxo",
      "score": 82.0,
      "langue": "fr",
      "secteur": "LUXE",
      "source": "llm"
    },
    ...
  ],
  "model_used": "mistral",
  "duree_ms": 18750.3
}
```

---

## 📊 Comparaison Détaillée

| Aspect | Mode A | Mode B |
|--------|--------|--------|
| **Vitesse** | ⚡ Ultra rapide (100ms) | 🐢 Lent (5-30s) |
| **Coût** | 💰 Gratuit | 💵 API/Subscription |
| **Qualité** | 📊 Moyenne | 🎨 Excellente |
| **Créativité** | 🔄 Reproductible | 🌈 Variable |
| **Localisation** | 🏠 100% Local | 🌐 Nécessite réseau |
| **Prompt requis** | ❌ Non | ✅ Oui |
| **Use Case** | Génération massive | Naming premium |
| **Cas d'Usage** | B2B Batch, Tests | B2C, Consultation |

---

## 🔧 Architecture Implémentation

### Mode A (existant)
```
POST /api/generate
├─ Router: backend/app/routers/generate.py
├─ Service: backend/app/services/nomgen_core.py
└─ Model: backend/app/weights/model_{lang}_{secteur}.pt
```

### Mode B (nouveau)
```
POST /api/generate-llm-simple
├─ Router: backend/app/routers/generate_llm.py
├─ Service: backend/app/services/ollama_service.py
└─ Provider: Ollama | OpenAI | Custom
```

---

## 🎯 Flux Utilisateur Frontend

### Mode A (Sélection Simple)
```
┌─────────────────────────────┐
│ Génération Automatique      │
├─────────────────────────────┤
│ Type:     ▼ Marque          │
│ Secteur:  ▼ Luxe            │
│ Langue:   ▼ Français        │
│ Nombre:   [10]              │
│                             │
│ [🚀 Générer]               │
│                             │
│ Résultats:                  │
│ • Luxora      (85)          │
│ • Syntaxo     (82)          │
│ • Pixelai     (79)          │
│ ...                         │
└─────────────────────────────┘
```

### Mode B (Prompt Libre)
```
┌─────────────────────────────┐
│ Génération Intelligente     │
├─────────────────────────────┤
│ Décrivez votre idée:        │
│ ┌───────────────────────┐   │
│ │ "Marque de luxe      │   │
│ │ français pour femmes │   │
│ │ 25-45 ans. Cosmé-   │   │
│ │ tiques naturels..."  │   │
│ └───────────────────────┘   │
│                             │
│ Langue: ▼ Français          │
│ Modèle: ▼ Mistral           │
│ Nombre: [10]                │
│                             │
│ [🚀 Générer]               │
│                             │
│ Résultats (via LLM):        │
│ • Naturelle      (88)       │
│ • Éclat Botanique (92)      │
│ • Essence Nature  (85)      │
│ ...                         │
└─────────────────────────────┘
```

---

## 📋 Checklist Implémentation

- [x] Mode A - Endpoint `/api/generate` existant
- [x] Mode B - Endpoint `/api/generate-llm-simple` créé
- [x] Service Ollama (httpx, 15 lignes)
- [x] Fallback OpenAI
- [ ] **Frontend React** - Deux formulaires distincts
- [ ] Support modèles arabes (Allam, Fanar)
- [ ] Documentation API complète
- [ ] Tests Mode A + B

---

## 🚀 Déploiement

### Local Development
```bash
# Mode A (toujours disponible)
python -m uvicorn app.main:app --reload

# Mode B avec Ollama
ollama serve &
ollama pull mistral
# API disponible sur localhost:11434

# Mode B avec OpenAI
export OPENAI_API_KEY="sk-..."
# Utilise fallback automatique
```

### Production
```bash
# Mode A: Fonctionne partout ✅
# Mode B: Options
  1. Ollama + GPU server
  2. OpenAI API
  3. Hugging Face Inference
  4. Custom LLM
```

---

## 💡 Recommandations d'Utilisation

### Quand utiliser Mode A?
- ✅ Tests rapides de concepts
- ✅ Génération massive (1000+ noms)
- ✅ Budget zéro
- ✅ Latence ultra-basse requise
- ✅ Reproduction des résultats

### Quand utiliser Mode B?
- ✅ Naming premium/consultation
- ✅ Besoin de contexte complexe
- ✅ Marques à fort potentiel commercial
- ✅ Multilingue avancé
- ✅ Créativité maximale
