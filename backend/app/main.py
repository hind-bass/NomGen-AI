"""
Point d'entrée FastAPI — NomGen AI v4.0
Jour 2 → Jour 4 : Tous les routers enregistrés.
"""
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

# Charger les clés API depuis backend/.env (OPENAI_API_KEY, MISTRAL_API_KEY, etc.)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from fastapi.middleware.cors import CORSMiddleware

# ── Routers Sprint 1-4 (génération nanoGPT) ──────────────────────────────────
from app.routers import generate, health, models_info

# ── Routers Jour 1 (auth + persistance) ──────────────────────────────────────
from app.routers.auth          import router as auth_router
from app.routers.favorites     import router as favorites_router
from app.routers.history       import router as history_router

# ── Routers Jour 2 (Mode B LLM) ──────────────────────────────────────────────
from app.routers.generate_llm  import router as generate_llm_router

# ── Routers Jour 3 (suggestions + réservations) ──────────────────────────────
from app.routers.suggestions   import router as suggestions_router
from app.routers.reservations  import router as reservations_router

# ── Routers Jour 4 (profil) ───────────────────────────────────────────────────
from app.routers.profile       import router as profile_router

# ── Routers Admin ──────────────────────────────────────────────────────────────
from app.routers.admin         import router as admin_router

# ── Routers Feedback & Favoris (votes) ───────────────────────────────────────
from app.api.feedback          import router as feedback_router
from app.api.favoris           import router as favoris_votes_router

# ── Base de données ───────────────────────────────────────────────────────────
from app.database import create_db_and_tables
from app.seeder   import seed_admin

app = FastAPI(
    title="NomGen AI API",
    description="Générateur de noms de marques FR/AR — nanoGPT + LLM + JWT Auth",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Enregistrement des routes ─────────────────────────────────────────────────

# Sprint 1-4
app.include_router(generate.router,        prefix="/api")
app.include_router(health.router,          prefix="/api")
app.include_router(models_info.router,     prefix="/api")

# Jour 1
app.include_router(auth_router)            # /auth/register  /auth/login
app.include_router(favorites_router)       # /api/favorites
app.include_router(history_router)         # /api/history

# Jour 2
app.include_router(generate_llm_router,    prefix="/api")   # /api/generate-llm
                                                             # /api/models/llm-list

# Jour 3
app.include_router(suggestions_router)     # /api/suggestions
app.include_router(reservations_router)    # /api/reservations

# Jour 4
app.include_router(profile_router)         # /api/profile

# Admin
app.include_router(admin_router)           # /api/admin/...

# Feedback & votes (SQLite : generations, feedback, favoris)
app.include_router(feedback_router)        # POST /feedback/like|dislike, GET /feedback/stats
app.include_router(favoris_votes_router)   # POST /favorites/add, GET /favorites


# ── Événement de démarrage ────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    """Initialise la DB et crée l'admin par défaut si absent."""
    create_db_and_tables()
    seed_admin()
    print("[NomGen] API v4.0 demarree [OK]")
    print("[NomGen] Swagger UI : http://localhost:8000/docs")


# ── Route racine ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Racine"])
async def root():
    return {
        "app": "NomGen AI",
        "version": "4.0.0",
        "endpoints": {
            "docs": "/docs",
            "generate_A": "POST /api/generate",
            "generate_B": "POST /api/generate-llm",
            "auth": "POST /auth/register | POST /auth/login",
            "favorites": "GET|POST|DELETE /api/favorites",
            "history": "GET /api/history",
            "suggestions": "POST|GET /api/suggestions",
            "admin_approve": "PATCH /api/suggestions/:id/approve",
            "admin_reject": "PATCH /api/suggestions/:id/reject",
            "reservations": "POST|GET /api/reservations",
            "profile": "GET /api/profile",
            "llm_models": "GET /api/models/llm-list",
            "admin_users": "POST|GET|PATCH|DELETE /api/admin/users/:id",
            "admin_suggestions_list": "GET /api/admin/suggestions",
            "admin_suggestions_add": "POST /api/admin/suggestions/add",
            "admin_suggestions_review": "PATCH /api/admin/suggestions/:id",
            "admin_reservations": "GET /api/admin/reservations",
            "admin_reservations_stats": "GET /api/admin/reservations/stats",
            "admin_reservation_update": "PATCH /api/admin/reservations/:id",
            "admin_reservation_delete": "DELETE /api/admin/reservations/:id",
            "admin_training_stats": "GET /api/admin/training/stats",
            "admin_training_export": "GET /api/admin/training/export",
            "admin_training_sync": "POST /api/admin/training/sync-datasets",
            "local_llm_models": "ollama-llama31 | ollama-qwen25 | ollama-mistral",
            "feedback_like": "POST /feedback/like",
            "feedback_dislike": "POST /feedback/dislike",
            "feedback_stats": "GET /feedback/stats",
            "favorites_add": "POST /favorites/add",
            "favorites_list": "GET /favorites",
        }
    }