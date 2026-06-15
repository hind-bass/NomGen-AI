"""
Point d'entrée FastAPI — NomGen AI v3.0
Jour 1 : Auth JWT + SQLite + Favoris persistants + Historique
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers existants
from app.routers import generate, health, models_info

# Nouveaux routers Jour 1
from app.routers.auth import router as auth_router
from app.routers.favorites import router as favorites_router
from app.routers.history import router as history_router

# Base de données
from app.database import create_db_and_tables
from app.seeder import seed_admin

app = FastAPI(
    title="NomGen AI API",
    description="Générateur de noms de marques FR/AR — nanoGPT + JWT Auth",
    version="3.0.0",
)

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────
# Routers existants (inchangés)
app.include_router(generate.router,     prefix="/api")
app.include_router(health.router,       prefix="/api")
app.include_router(models_info.router,  prefix="/api")

# Nouveaux routers Jour 1
app.include_router(auth_router)          # /auth/register, /auth/login
app.include_router(favorites_router)     # /api/favorites
app.include_router(history_router)       # /api/history


# ─── Événement de démarrage ───────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    """Crée les tables SQLite et l'admin par défaut au premier démarrage."""
    create_db_and_tables()
    seed_admin()
    print("[NomGen] API démarrée — DB prête ✓")


@app.get("/")
async def root():
    return {
        "message": "NomGen AI API v3.0",
        "docs": "/docs",
        "auth": "POST /auth/register | POST /auth/login",
    }
