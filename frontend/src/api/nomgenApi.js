import axios from "axios";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api",
  timeout: 15000,
});

export const generateNames = async (params) => {
  const { data } = await API.post("/generate", {
    prompt:      params.prompt      || "",
    secteur:     params.secteur     || "LUXE",
    langue:      params.langue      || "fr",
    n:           params.n           || 10,
    temperature: params.temperature || 1.0,
    top_k:       params.topK        || 20,
    seed:        params.seed        || null,
  });
  return data;
};

export const getHealth    = ()  => API.get("/health");
export const getModelsInfo = () => API.get("/models");
