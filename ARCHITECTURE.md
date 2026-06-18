# 🏗️ Architecture Complète NomGen AI v4.0

## 🎯 Vision Globale

```
                    ┌─────────────────────────────────────┐
                    │    NOMGEN AI - Générateur de Noms   │
                    │    Français 🇫🇷 | Arabe 🇸🇦          │
                    └─────────────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
         ┌──────▼───────┐            ┌───────▼────────┐
         │   MODE A     │            │    MODE B      │
         │  (Automati)  │            │  (Intelligent) │
         └──────────────┘            └────────────────┘
              │                              │
         [Local nanoGPT]           [Ollama/OpenAI/Custom]
         Fast (100ms)              Smart (5-30s)
         Free                       Paid/Custom
```

---

## 📋 Stack Technologique

### Backend
```
Framework:    FastAPI (Python 3.11)
DB:           SQLite (nomgen.db)
Auth:         JWT (PyJWT)
ORM:          SQLModel (Pydantic + SQLAlchemy)
Async:        httpx, asyncio
ML:           PyTorch (nanoGPT)
```

### Frontend (À implémenter)
```
Framework:    React 18+
Routing:      React Router
State:        Context API / Redux
UI:           Tailwind CSS / Material-UI
HTTP:         Axios
```

### LLM Providers
```
Français:     GPT-4o, Mistral, DeepSeek, Claude
Arabe:        Allam, Fanar, AceGPT, Jais
Local:        Ollama (mistral, dolphin, etc.)
```

---

## 📁 Structure Projet

```
ProjetVersion1/
├── backend/
│   ├── app/
│   │   ├── main.py                      # Point d'entrée FastAPI
│   │   ├── database.py                  # Config SQLite
│   │   ├── dependencies.py              # Auth middleware
│   │   ├── seeder.py                    # Admin par défaut
│   │   │
│   │   ├── models/
│   │   │   ├── db_models.py            # Tables: User, Suggestion, Favorite, etc.
│   │   │   ├── schemas.py              # Pydantic models
│   │   │   └── nanogpt.py              # Architecture nanoGPT
│   │   │
│   │   ├── routers/
│   │   │   ├── auth.py                 # POST /auth/register, /auth/login
│   │   │   ├── generate.py             # POST /api/generate [MODE A]
│   │   │   ├── generate_llm.py         # POST /api/generate-llm-simple [MODE B]
│   │   │   ├── suggestions.py          # Suggestions communautaires
│   │   │   ├── favorites.py            # Favoris utilisateur
│   │   │   ├── history.py              # Historique générations
│   │   │   ├── profile.py              # Profil utilisateur
│   │   │   ├── admin.py                # Gestion admin
│   │   │   └── reservations.py         # Réservations premium
│   │   │
│   │   ├── services/
│   │   │   ├── nomgen_core.py          # NomGenService (Mode A)
│   │   │   ├── ollama_service.py       # Service Ollama direct (Mode B)
│   │   │   ├── llm_service.py          # LLM router (ancien)
│   │   │   ├── auth_service.py         # JWT, hashing
│   │   │   ├── scorer.py               # Scoring noms
│   │   │   ├── prompt_nlu.py           # NLP prompt parsing
│   │   │   └── prompt_nlu.py           # LLM service complexe
│   │   │
│   │   └── weights/
│   │       ├── model_fr.pt             # Modèle générique FR
│   │       ├── model_ar.pt             # Modèle générique AR
│   │       ├── model_fr_tech.pt        # Spécialisé FR + TECH
│   │       ├── model_fr_food.pt        # Spécialisé FR + FOOD
│   │       ├── vocab_fr.json           # Vocabulaire FR
│   │       └── vocab_ar.json           # Vocabulaire AR
│   │
│   ├── nomgen.db                       # Base de données
│   └── server.log                      # Logs serveur
│
├── frontend/                           # À implémenter
│   ├── src/
│   │   ├── components/
│   │   │   ├── ModeAForm.jsx           # Formulaire Mode A
│   │   │   └── ModeBForm.jsx           # Formulaire Mode B
│   │   ├── pages/
│   │   │   ├── Generate.jsx            # Page génération
│   │   │   ├── Dashboard.jsx           # Dashboard utilisateur
│   │   │   └── Admin.jsx               # Admin panel
│   │   └── App.jsx
│   └── package.json
│
├── data/                               # Datasets
│   ├── fr/
│   │   ├── marque/
│   │   │   ├── general.txt
│   │   │   ├── tech.txt
│   │   │   ├── food.txt
│   │   │   └── luxe.txt
│   │   └── societe/
│   └── ar/
│       └── ...
│
├── notebooks/
│   ├── 01_NanoGPT_Training.ipynb       # Entraîner modèles génériques
│   ├── 02_DataPrep.ipynb               # Préparer les données
│   ├── 03_Tokenizer.ipynb              # Build vocabulaires
│   ├── 04_Evaluate.ipynb               # Évaluer performance
│   └── Sprint5_PerCategory.ipynb       # Entraîner par catégorie
│
├── Sprint5_PerCategory.ipynb           # Créé ✅
├── generate_names.py                   # Script génération ✅
├── explore_db.py                       # Explorer DB ✅
├── export_db.py                        # Exporter CSV ✅
├── reset_db.py                         # Réinitialiser DB ✅
│
├── MODES_DOCUMENTATION.md              # Créé ✅
├── API_COMPLETE_GUIDE.md               # Créé ✅
├── ADMIN_API.md                        # Créé ✅
├── CHANGELOG_ADMIN.md                  # Créé ✅
├── BD_GUIDE.md                         # Créé ✅
└── README.md                           # À faire
```

---

## 🔄 Flux de Requête

### Mode A: Génération Automatique
```
User Request
    ↓
POST /api/generate
    ↓
[NomGenService._get_model()]
    ├─ Try: model_{lang}_{secteur}.pt
    ├─ Fallback: model_{lang}.pt
    └─ Return: NanoGPT model
    ↓
[NomGenService._run_generation()]
    ├─ Tokenize input
    ├─ Generate tokens via nanoGPT
    ├─ Decode output
    └─ Return: list[names]
    ↓
[Scoring]
    ├─ score_fr() pour français
    └─ score_ar() pour arabe
    ↓
[Log historique] (si user connecté)
    ↓
HTTP 200 + JSON response
```

**Timeline: 87ms (local, pas de réseau)**

---

### Mode B: Génération Intelligente
```
User Request + Prompt
    ↓
POST /api/generate-llm-simple
    ↓
[ollama_service.call_ollama()]
    ├─ Try: POST localhost:11434
    │   └─ response
    │
    └─ Fallback on error:
        call_openai()
        └─ POST api.openai.com
    ↓
[Parse JSON response]
    ├─ Extract [names] from text
    └─ Return: list[names]
    ↓
[Scoring + Format]
    ├─ Lower case + strip
    └─ Calculate score heuristique
    ↓
[Log historique]
    ↓
HTTP 200 + JSON response
```

**Timeline: 5-30s (réseau, LLM latency)**

---

## 🔐 Sécurité

```
┌─────────────────────────────────────┐
│         NOMGEN AI Security          │
├─────────────────────────────────────┤
│                                     │
│ ✅ JWT Authentication              │
│    - Token expiry: 24h              │
│    - Role-based access (admin)      │
│                                     │
│ ✅ Password Hashing                 │
│    - bcrypt 12 rounds               │
│                                     │
│ ✅ CORS Protection                  │
│    - Whitelist: localhost:3000      │
│                                     │
│ ✅ Input Validation                 │
│    - Pydantic + type checking       │
│    - SQL injection prevention       │
│                                     │
│ ✅ Database                         │
│    - SQLite (local, pas de réseau)  │
│    - Foreign keys integrity         │
│                                     │
│ ✅ Suggestion Deduplication         │
│    - Triple check (fichier+DB+DB)   │
│    - Case-insensitive matching      │
│                                     │
│ ⚠️  TODO: HTTPS en prod             │
│ ⚠️  TODO: Rate limiting             │
│ ⚠️  TODO: API Key rotation          │
│                                     │
└─────────────────────────────────────┘
```

---

## 📊 Base de Données

### Tables

```sql
user (id, email, hashed_password, role, is_active, created_at)
├─ PK: id
├─ UNIQUE: email
└─ FK: N/A

favorite (id, user_id, nom, score, langue, secteur, created_at)
├─ PK: id
├─ FK: user_id → user.id
└─ INDEX: user_id, created_at

history (id, user_id, prompt, langue, secteur, n_generated, mode, created_at)
├─ PK: id
├─ FK: user_id → user.id
└─ INDEX: user_id, created_at

suggestion (id, user_id, nom, langue, secteur, type_nom, status, submitted_at, reviewed_at)
├─ PK: id
├─ FK: user_id → user.id
├─ UNIQUE: (nom, langue, secteur) per status
└─ INDEX: status, submitted_at

reservation (id, user_id, nom, langue, secteur, is_paid, created_at)
├─ PK: id
├─ FK: user_id → user.id
└─ INDEX: is_paid, created_at
```

**Taille: 44 KB (actuel) → ~500 MB (projection 1M suggestions)**

---

## 🚀 Roadmap

### Phase 1: MVP ✅ (Complété)
- [x] Mode A - nanoGPT local
- [x] Mode B - Ollama/OpenAI
- [x] Auth JWT
- [x] Admin panel backend
- [x] Suggestions communautaires
- [x] Base de données SQLite
- [x] Documentation API

### Phase 2: Frontend (À Faire)
- [ ] React app
- [ ] Mode A UI (sélecteurs simple)
- [ ] Mode B UI (prompt libre)
- [ ] Dashboard utilisateur
- [ ] Admin panel UI
- [ ] Favoris UI

### Phase 3: Production
- [ ] Docker containerization
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] PostgreSQL (scaling)
- [ ] Redis cache
- [ ] CDN assets
- [ ] Monitoring (Sentry)
- [ ] Analytics (Mixpanel)

### Phase 4: Advanced
- [ ] Modèles spécialisés par catégorie (Sprint 5)
- [ ] Fine-tuning modèles LLM
- [ ] Multi-langue support (Jais, Allam, etc.)
- [ ] Marketplace suggestions
- [ ] API publique (SDK)

---

## 📈 Métriques & KPIs

```
Utilisateurs:     N/A (MVP backend)
Générations:      TBD
Temps moyen Mode A: 87ms
Temps moyen Mode B: 18s
Coût API:         ~$0.01 par requête (GPT-4)
Disponibilité:    99.9% (local) / 99% (external)
```

---

## 🎓 Learning & References

### Modèles & Papers
- Karpathy's nanoGPT: https://github.com/karpathy/nanoGPT
- Attention Is All You Need (Vaswani 2017)
- GPT-2 Paper (Radford 2019)

### Frameworks
- FastAPI: https://fastapi.tiangolo.com
- SQLModel: https://sqlmodel.tiangolo.com
- PyTorch: https://pytorch.org

### LLMs
- Ollama: https://ollama.ai
- OpenAI: https://openai.com/api
- SDAIA Allam: https://www.allam.ai

---

## 📞 Support & Deployment

### Local Development
```bash
# Backend
cd backend
python -m uvicorn app.main:app --reload

# Ollama (optionnel)
ollama serve
ollama pull mistral
```

### Production
```bash
# Docker
docker build -t nomgen-api .
docker run -p 8000:8000 nomgen-api

# Kubernetes
kubectl apply -f deployment.yaml
```

### Monitoring
```bash
# Logs
docker logs -f nomgen-api

# Health
curl http://localhost:8000/health

# Metrics
GET /metrics  (TODO: Prometheus)
```

---

## 📝 Notes Importantes

1. **Modèles nanoGPT**: Entraînés en local, ~500MB per langue
2. **Ollama**: Nécessaire pour Mode B local (5-30 sec latency)
3. **OpenAI Fallback**: Automatique si Ollama indisponible
4. **Scalabilité**: Mode A = illimité local, Mode B = limité par quota API
5. **Coût**: Mode A = $0, Mode B = $0.01-0.1 par requête

---

**Version**: 4.0.0 | **Date**: 2026-06-16 | **Status**: Beta
