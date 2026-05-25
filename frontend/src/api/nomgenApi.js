import axios from "axios";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api",
  timeout: 15000,
});

/**
 * Génère des noms de marques / sociétés via le backend FastAPI.
 *
 * Paramètres attendus :
 *   params.prompt      {string}  Texte libre de l'utilisateur
 *   params.type        {string}  "marque" | "societe"
 *   params.category    {string}  "general" | "luxe" | "tech" | "food" | "services" | "industrie"
 *   params.langue      {string}  "fr" | "ar"
 *   params.n           {number}  Nombre de noms souhaités
 *   params.temperature {number}  Créativité (0.1 – 2.5)
 *   params.topK        {number}  Top-K sampling
 *   params.seed        {number?} Graine aléatoire (optionnel)
 */
export const generateNames = async (params) => {
  const { data } = await API.post("/generate", {
    prompt:     params.prompt       || "",
    type:       params.type         || "marque",
    category:   params.category     || "general",
    langue:     params.langue       || "fr",
    n:          params.n            ?? 10,
    temperature: params.temperature ?? 1.0,
    top_k:      params.topK         ?? 20,
    seed:       params.seed         ?? null,
  });
  return data;
};

export const getHealth     = () => API.get("/health");
export const getModelsInfo = () => API.get("/models");