# BrandForge / NomGen AI

Générateur de noms de marques et d'entreprises (FR/AR) — nanoGPT + LLM + auth JWT.

## Structure du projet

```
ProjetVersion1/
├── backend/          # API FastAPI (auth, génération, admin, feedback)
│   ├── app/
│   │   ├── api/          # Feedback & favoris (fine-tuning)
│   │   ├── database/     # SQLite / SQLModel
│   │   ├── models/       # Tables & schémas Pydantic
│   │   ├── routers/      # Routes REST principales
│   │   ├── schemas/      # DTO feedback
│   │   ├── services/     # Logique métier & ML
│   │   └── weights/      # Modèles nanoGPT (.pt)
│   └── tests/
├── frontend/         # React + Vite + Tailwind
│   └── src/
│       ├── components/
│       ├── config/       # API_BASE centralisé
│       ├── context/
│       └── assets/
├── data/             # Datasets noms (.txt) par langue/secteur/type
├── docs/             # Documentation détaillée
├── notebooks/        # Entraînement nanoGPT (Sprint 1–5)
└── scripts/          # Utilitaires CLI (split, check, reset DB)
```

## Démarrage rapide

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

- API : http://127.0.0.1:8000/docs  
- Frontend : http://localhost:5173  
