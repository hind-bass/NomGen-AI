from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum


class CreativityPreset(str, Enum):
    CONSERVATEUR = "conservative"
    EQUILIBRE = "balanced"
    CREATIF = "creative"


class EntityType(str, Enum):
    MARQUE = "marque"
    SOCIETE = "societe"


class GenerateRequest(BaseModel):
    prompt:              str
    type:                EntityType
    category:            str
    langue:              str                     = "fr"
    n:                   int                     = Field(10, ge=1, le=50)
    creativity_preset:   Optional[CreativityPreset] = CreativityPreset.EQUILIBRE
    temperature:         Optional[float]         = None
    top_k:               Optional[int]           = None
    top_p:               Optional[float]         = None
    repetition_penalty:  Optional[float]         = 1.0
    seed:                Optional[int]           = None

    @validator('category')
    def validate_category(cls, v, values):
        from ..config import CATEGORIES_CONFIG
        type_ = values.get('type')
        if type_:
            type_value = type_.value if hasattr(type_, 'value') else str(type_)
            valid_cats = [s['id'] for s in CATEGORIES_CONFIG['categories'][type_value]['sectors']]
            if v not in valid_cats:
                raise ValueError(f"Invalid category '{v}' for type '{type_value}'")
        return v


class GeneratedName(BaseModel):
    nom:      str
    score:    float
    langue:   str
    category: str
    type:     str


class GenerateResponse(BaseModel):
    noms:             List[GeneratedName]
    strategy_used:    str
    category_hint:    str
    duree_ms:         float


class HealthResponse(BaseModel):
    status:  str
    version: str
    models:  List[str]
