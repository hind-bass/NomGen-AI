import { useState, useCallback } from "react";
import { generateNames } from "../api/nomgenApi";

/**
 * Hook de génération de noms.
 * Utilisé par Generator.jsx (vue liste) ET CardsScreen.jsx (vue swipe).
 *
 * Retourne :
 *   results   — tableau de GeneratedName [{nom, score, langue, secteur, type}]
 *   loading   — booléen
 *   error     — message d'erreur ou null
 *   duration  — temps de génération en ms (null si pas encore généré)
 *   generate  — fonction (params) => Promise
 *   clear     — remet les résultats à zéro
 */
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
      setResults(data.noms ?? []);
      setDuration(data.duree_ms ?? null);
    } catch (err) {
      // Distinguer erreur réseau (backend éteint) et erreur applicative
      if (!err.response) {
        setError("Impossible de joindre le backend. Vérifiez que le serveur tourne sur le port 8000.");
      } else {
        setError(err.response?.data?.detail || "Erreur lors de la génération.");
      }
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setResults([]);
    setError(null);
    setDuration(null);
  }, []);

  return { results, loading, error, duration, generate, clear };
}