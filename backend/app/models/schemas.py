from pydantic import BaseModel, Field
from typing import Optional, List


class GenerateRequest(BaseModel):
    prompt:      Optional[str]   = ""
    secteur:     Optional[str]   = "LUXE"
    langue:      str             = "fr"
    n:           int             = Field(10, ge=1, le=50)
    temperature: float           = Field(1.0, ge=0.1, le=2.5)
    top_k:       int             = Field(20, ge=1, le=100)
    seed:        Optional[int]   = None


class GeneratedName(BaseModel):
    nom:     str
    score:   float
    langue:  str
    secteur: str


class GenerateResponse(BaseModel):
    noms:             List[GeneratedName]
    tokens_detectes:  List[str]
    duree_ms:         float


class HealthResponse(BaseModel):
    status:  str
    version: str
    models:  List[str]
