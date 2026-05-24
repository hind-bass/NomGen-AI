import os
from fastapi import APIRouter

router = APIRouter()

WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "..", "weights")


def _parse_model_tag(filename: str) -> dict:
    """
    Extrait les métadonnées d'un nom de fichier .pt.

    Exemples :
      model_fr.pt               → {lang:'fr', type:'unified', secteur:'all'}
      model_fr_marque_luxe.pt   → {lang:'fr', type:'marque',  secteur:'luxe'}
      model_ar_societe_tech.pt  → {lang:'ar', type:'societe', secteur:'tech'}
    """
    tag   = filename.replace("model_", "").replace(".pt", "")
    parts = tag.split("_")
    return {
        "id":      tag,
        "lang":    parts[0] if len(parts) > 0 else "?",
        "type":    parts[1] if len(parts) > 1 else "unified",
        "secteur": parts[2] if len(parts) > 2 else "all",
        "file":    filename,
    }


@router.get("/models")
async def models_info():
    """
    Liste tous les modèles .pt disponibles dans backend/app/weights/.
    Auto-découverte : pas besoin de mettre à jour ce fichier
    quand un nouveau modèle est ajouté.
    """
    if not os.path.exists(WEIGHTS_DIR):
        return {"count": 0, "models": [], "error": "weights/ introuvable"}

    pt_files = sorted(f for f in os.listdir(WEIGHTS_DIR) if f.endswith(".pt"))
    models   = [_parse_model_tag(f) for f in pt_files]

    return {
        "count":    len(models),
        "models":   models,
        "langs":    sorted({m["lang"]    for m in models}),
        "types":    sorted({m["type"]    for m in models}),
        "secteurs": sorted({m["secteur"] for m in models}),
    }