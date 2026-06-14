from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import generate, health, models_info, analyze_prompt  # + analyze_prompt

from app.models.db import create_db
from app.routers import auth
app.include_router(auth.router, prefix="/api")

from app.routers import user_data
app.include_router(user_data.router, prefix="/api")
app = FastAPI(
    title="NomGen AI API",
    description="Générateur de noms de marques FR/AR — nanoGPT",
    version="3.0.0",
)
@app.on_event("startup")
def on_startup():
    create_db()
    print(" Base de données SQLite prête")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router,        prefix="/api")
app.include_router(health.router,          prefix="/api")
app.include_router(models_info.router,     prefix="/api")
app.include_router(analyze_prompt.router,  prefix="/api")   # nouveau


@app.get("/")
async def root():
    return {"message": "NomGen AI API v3.0", "docs": "/docs"}