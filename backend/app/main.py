from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import generate, health, models_info

app = FastAPI(
    title="NomGen AI API",
    description="Générateur de noms de marques FR/AR — nanoGPT",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router,    prefix="/api")
app.include_router(health.router,      prefix="/api")
app.include_router(models_info.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "NomGen AI API — docs: /docs"}
