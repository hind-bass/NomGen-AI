import { useState, useCallback } from "react";
import { generateNames } from "../api/nomgenApi";

export function useGenerator() {
  const [results,  setResults]  = useState([]);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);
  const [duration, setDuration] = useState(null);

  const generate = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    try {
      const data = await generateNames(params);
      setResults(data.noms);
      setDuration(data.duree_ms);
    } catch (err) {
      setError(err.response?.data?.detail || "Erreur de connexion au backend");
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = () => { setResults([]); setError(null); setDuration(null); };
  return { results, loading, error, duration, generate, clear };
}
