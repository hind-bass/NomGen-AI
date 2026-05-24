import axios from "axios";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api",
  timeout: 15000,
});

// ── Style UI → secteur backend ─────────────────────────────────────────────
// Les labels affichés dans le frontend (clé minuscule) → valeurs attendues
// par nomgen_core.py pour sélectionner le bon modèle .pt
const STYLE_TO_SECTEUR = {
  futuriste: "tech",
  luxe:      "luxe",
  tech:      "tech",
  minimal:   "general",
  tous:      "general",
  nature:    "general",
  corporate: "services",
  playful:   "general",
};

/**
 * Normalise un style UI en secteur backend.
 * Accepte à la fois "Luxe" (depuis le frontend) et "luxe" (direct).
 */
export function resolveStyle(style) {
  if (!style) return "general";
  const key = style.toLowerCase().trim();
  return STYLE_TO_SECTEUR[key] ?? key;
}

/**
 * Génère des noms de marques / sociétés via le backend FastAPI.
 *
 * Paramètres attendus :
 *   params.prompt          {string}  Texte libre de l'utilisateur
 *   params.style           {string}  Label UI : "Luxe", "Tech", "Tous"…
 *   params.generationType  {string}  "marque" | "entreprise"
 *   params.langue          {string}  "fr" | "ar"
 *   params.n               {number}  Nombre de noms souhaités
 *   params.temperature     {number}  Créativité (0.1 – 2.5)
 *   params.topK            {number}  Top-K sampling
 *   params.seed            {number?} Graine aléatoire (optionnel)
 */
export const generateNames = async (params) => {
  const { data } = await API.post("/generate", {
    prompt:          params.prompt                   || "",
    secteur:         resolveStyle(params.style ?? params.secteur),
    generation_type: params.generationType           || "marque",
    langue:          params.langue                   || "fr",
    n:               params.n                        ?? 10,
    temperature:     params.temperature              ?? 1.0,
    top_k:           params.topK                     ?? 20,
    seed:            params.seed                     ?? null,
  });
  return data;
};

export const getHealth     = () => API.get("/health");
export const getModelsInfo = () => API.get("/models");