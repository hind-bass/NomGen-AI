"""
Interpréteur de prompt avancé — v2.0
Détection automatique : langue (FR/AR) + secteur + type (marque/societe).

Nouveautés vs v1 :
  - detect_language() : analyse la proportion Arabic Unicode vs Latin
  - Mots-clés arabes ajoutés à chaque secteur
  - Détection du type (marque / societe) via mots-clés bilingues
  - PromptAnalysis : dataclass de retour structuré
  - analyze_prompt() : point d'entrée principal pour l'API
  - parse_prompt() : conservée à l'identique pour rétrocompatibilité
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field


# ── Détection de langue ───────────────────────────────────────────────────────
_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")   # Bloc arabe de base
_LATIN_RE  = re.compile(r"[a-zA-ZÀ-ÿ]")


def detect_language(text: str) -> tuple[str, float]:
    """
    Analyse la proportion de caractères arabes vs latins.
    Retourne (langue, confiance) où confiance ∈ [0.5, 1.0].

    Exemples :
      "startup tech moderne"  → ("fr", 1.0)
      "شركة تقنية حديثة"       → ("ar", 1.0)
      "marque luxe / فاخر"    → ("fr", 0.67)  # majorité latine
    """
    arabic_n = len(_ARABIC_RE.findall(text))
    latin_n  = len(_LATIN_RE.findall(text))
    total    = arabic_n + latin_n

    if total == 0:
        return "fr", 0.5

    ar_ratio = arabic_n / total
    if ar_ratio >= 0.5:
        return "ar", round(ar_ratio, 2)
    return "fr", round(1.0 - ar_ratio, 2)


# ── Mots-clés secteur (FR + AR mélangés) ─────────────────────────────────────
SECTEUR_KEYWORDS: dict[str, list[str]] = {
    "luxe": [
        # Français
        "luxe", "luxueux", "haut de gamme", "premium", "prestige", "mode",
        "fashion", "couture", "bijou", "joaillerie", "parfum", "beaute",
        "elegance", "raffiné", "somptueux", "opulent", "haute couture",
        # Arabe
        "فاخر", "راقي", "أناقة", "فخامة", "رفاهية", "مرموق", "عريق",
        "كماليات", "فخم", "ثمين",
    ],
    "tech": [
        # Français
        "tech", "technologie", "digital", "numerique", "app", "application",
        "software", "ia", "intelligence artificielle", "data", "startup",
        "innovation", "web", "saas", "cloud", "logiciel", "plateforme",
        "algorithme", "intelligence", "code", "developpement", "mobile",
        # Arabe
        "تقنية", "تكنولوجيا", "ذكاء اصطناعي", "برمجة", "تطبيق", "ابتكار",
        "رقمي", "شبكة", "بيانات", "ذكي", "تطوير", "منصة",
    ],
    "food": [
        # Français
        "food", "alimentaire", "nourriture", "cuisine", "gastronomie",
        "gourmet", "boisson", "eau", "jus", "yaourt", "fromage", "epicerie",
        "snack", "restaurant", "bio", "vegan", "saveur", "gourmand",
        # Arabe
        "غذاء", "طعام", "مطبخ", "طبخ", "مأكولات", "مشروب", "مطعم",
        "أكل", "تغذية", "شهية",
    ],
    "services": [
        # Français
        "service", "conseil", "consulting", "agence", "cabinet", "audit",
        "finance", "banque", "assurance", "immobilier", "juridique", "droit",
        "rh", "ressources humaines", "recrutement", "formation", "transport",
        "sante", "médical", "clinique",
        # Arabe
        "خدمات", "استشارة", "وكالة", "مالي", "بنك", "تأمين", "توظيف",
        "تدريب", "صحة", "عيادة",
    ],
    "industrie": [
        # Français
        "industrie", "industriel", "automobile", "aeronautique",
        "construction", "batiment", "mecanique", "electronique", "energie",
        "btp", "engineering", "ingenierie", "fabrication", "usine", "acier",
        # Arabe
        "صناعة", "بناء", "تشييد", "طاقة", "هندسة", "تصنيع", "معادن",
        "مصنع", "إنشاء",
    ],
    "general": [
        # Secteur fallback : peu de mots-clés, score toujours bas
        "nom", "marque", "société", "entreprise", "business", "projet",
    ],
}

# Correspondance secteur → token legacy (rétrocompatibilité v1)
_SECTEUR_TO_TOKEN: dict[str, str] = {
    "luxe":      "#L",
    "tech":      "#T",
    "food":      "#F",
    "services":  "#P",
    "industrie": "#I",
    "general":   "#L",
}


# ── Mots-clés type (marque / societe) ─────────────────────────────────────────
_TYPE_KEYWORDS: dict[str, list[str]] = {
    "societe": [
        "société", "societe", "entreprise", "agence", "cabinet", "groupe",
        "compagnie", "firme", "corporation", "holding", "sarl", "sas", "inc",
        "شركة", "مؤسسة", "مجموعة", "مكتب", "هيئة",
    ],
    "marque": [
        "marque", "produit", "collection", "ligne", "gamme", "label",
        "brand", "identite", "logo", "nom de produit",
        "علامة", "منتج", "علامة تجارية",
    ],
}


# ── Résultat structuré ────────────────────────────────────────────────────────
@dataclass
class PromptAnalysis:
    langue:           str          # "fr" | "ar"
    secteur:          str          # "luxe" | "tech" | "food" | "services" | "industrie" | "general"
    generation_type:  str          # "marque" | "societe"
    ctrl_token:       str          # Legacy : "#L", "#T", …
    confidence_lang:  float        # ratio script dominant [0.5, 1.0]
    confidence_sect:  float        # score normalisé [0.0, 1.0]
    keywords_found:   list[str] = field(default_factory=list)


# ── Fonctions internes ────────────────────────────────────────────────────────
def _score_secteurs(text_lower: str) -> tuple[str, float, list[str]]:
    """Compte les mots-clés par secteur et retourne le meilleur."""
    scores: dict[str, int]        = {}
    hits_map: dict[str, list[str]] = {}

    for sect, keywords in SECTEUR_KEYWORDS.items():
        hits            = [kw for kw in keywords if kw in text_lower]
        scores[sect]    = len(hits)
        hits_map[sect]  = hits

    # Si aucun keyword trouvé, retourner "general" directement
    if all(s == 0 for s in scores.values()):
        return "general", 0.0, []

    # "general" ne gagne que s'il a strictement plus de hits (évite le fallback abusif)
    best = max(
        scores,
        key=lambda s: (scores[s] if s != "general" else scores[s] - 0.5),
    )
    best_score = scores[best]
    found      = hits_map[best]

    # Normalisation améliorée : plus sensible aux keywords importants
    # Min 0.5 si au moins 1 keyword trouvé (sauf "general")
    # Max 1.0 avec assez de keywords
    if best_score == 0:
        confidence = 0.0
    elif best == "general":
        confidence = min(best_score / 8, 1.0)  # Plus strict pour "general"
    else:
        # Pour secteurs spécialisés : min 0.5 avec 1 keyword, monte vers 1.0
        confidence = min(0.5 + (best_score / 6), 1.0)

    return best, round(confidence, 2), found


def _detect_type(text_lower: str) -> str:
    """Retourne "societe" ou "marque" selon les mots-clés présents."""
    for type_, keywords in _TYPE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return type_
    return "marque"  # défaut


# ── API publique ──────────────────────────────────────────────────────────────
def analyze_prompt(prompt: str) -> PromptAnalysis:
    """
    Analyse complète d'un prompt libre.
    Retourne un PromptAnalysis avec langue, secteur, type, token legacy
    et métriques de confiance.
    """
    if not prompt or not prompt.strip():
        return PromptAnalysis(
            langue="fr", secteur="general", generation_type="marque",
            ctrl_token="#L", confidence_lang=0.5, confidence_sect=0.0,
        )

    langue, conf_lang = detect_language(prompt)
    text_lower        = prompt.lower()
    secteur, conf_sect, found = _score_secteurs(text_lower)
    gen_type          = _detect_type(text_lower)
    ctrl              = _SECTEUR_TO_TOKEN.get(secteur, "#L")

    return PromptAnalysis(
        langue=langue,
        secteur=secteur,
        generation_type=gen_type,
        ctrl_token=ctrl,
        confidence_lang=conf_lang,
        confidence_sect=conf_sect,
        keywords_found=found,
    )


def parse_prompt(prompt: str, top_n: int = 2) -> list[str]:
    """
    Rétrocompatibilité v1 — utilisée par nomgen_core._run_generation().
    Retourne une liste de tokens legacy comme ["#L", "#T"].
    """
    if not prompt:
        return ["#L"]

    text_lower = prompt.lower()
    scores = {
        sect: sum(1 for kw in kws if kw in text_lower)
        for sect, kws in SECTEUR_KEYWORDS.items()
    }
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    result = [
        _SECTEUR_TO_TOKEN.get(s, "#L")
        for s, sc in ranked[:top_n]
        if sc > 0
    ]
    return result if result else ["#L"]