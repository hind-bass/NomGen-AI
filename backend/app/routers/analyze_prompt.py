"""
Router : POST /api/analyze-prompt
Expose l'analyse NLU du prompt à l'interface React.
Utile pour afficher "Langue détectée : FR • Secteur : Luxe" avant génération.
"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.prompt_nlu import analyze_prompt as _analyze

router = APIRouter()


class AnalyzeRequest(BaseModel):
    prompt: str


class AnalyzeResponse(BaseModel):
    langue:           str
    secteur:          str
    generation_type:  str
    ctrl_token:       str
    confidence_lang:  float
    confidence_sect:  float
    keywords_found:   list[str]


@router.post("/analyze-prompt", response_model=AnalyzeResponse)
async def analyze_prompt_endpoint(req: AnalyzeRequest):
    """
    Analyse un prompt libre et retourne :
      - langue        : "fr" | "ar"  (détecté automatiquement)
      - secteur       : "luxe" | "tech" | "food" | "services" | "industrie" | "general"
      - generation_type : "marque" | "societe"
      - ctrl_token    : token legacy "#L", "#T"… (pour debug)
      - confidence_lang : confiance sur la langue [0.5, 1.0]
      - confidence_sect : confiance sur le secteur [0.0, 1.0]
      - keywords_found  : mots-clés détectés dans le prompt
    """
    result = _analyze(req.prompt)
    return AnalyzeResponse(
        langue=result.langue,
        secteur=result.secteur,
        generation_type=result.generation_type,
        ctrl_token=result.ctrl_token,
        confidence_lang=result.confidence_lang,
        confidence_sect=result.confidence_sect,
        keywords_found=result.keywords_found,
    )