"""Interpréteur de prompt utilisateur → tokens de contrôle."""

KEYWORD_MAP = {
    "#L": ["luxe","luxueux","haut de gamme","premium","prestige","mode","fashion",
           "couture","bijou","joaillerie","parfum","beaute","elegance"],
    "#T": ["tech","technologie","digital","numerique","app","application","software",
           "ia","intelligence","data","startup","innovation","web","saas","cloud"],
    "#F": ["food","alimentaire","nourriture","cuisine","gastronomie","gourmet",
           "boisson","eau","jus","yaourt","fromage","epicerie","snack"],
    "#B": ["bio","biologique","naturel","ecologique","vert","durable","green",
           "eco","organique","vegan","vegetal","plante","herbe"],
    "#P": ["sante","pharmaceutique","medecine","cosmetique","soin","creme",
           "serum","lotion","pharmacie","medicament","complement","vitamine"],
    "#I": ["industrie","industriel","automobile","aeronautique","construction",
           "batiment","mecanique","electronique","energie"],
}


def parse_prompt(prompt: str, top_n: int = 2) -> list[str]:
    """Retourne les tokens de contrôle les plus pertinents pour un prompt."""
    if not prompt:
        return ["#L"]
    pl     = prompt.lower()
    scores = {tok: sum(1 for kw in kws if kw in pl)
              for tok, kws in KEYWORD_MAP.items()}
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    result = [tok for tok, sc in ranked[:top_n] if sc > 0]
    return result if result else ["#L"]
