import { useState, useCallback } from "react";
import { generateNames } from "../api/nomgenApi";

/**
 * Hook de génération de noms.
 * currentIndex est géré ici pour éviter tout setState synchrone dans useEffect.
 *
 * Retourne :
 *   results      — tableau de GeneratedName [{nom, score, langue, secteur, type}]
 *   loading      — booléen
 *   error        — message d'erreur ou null
 *   duration     — temps de génération en ms (null si pas encore généré)
 *   currentIndex — index de la carte courante
 *   setCurrentIndex — setter de l'index
 *   generate     — fonction (params) => Promise  (reset automatique de l'index)
 *   clear        — remet tout à zéro
 */
export function useGenerator() {
  const [results,       setResults]       = useState([]);
  const [loading,       setLoading]       = useState(false);
  const [error,         setError]         = useState(null);
  const [duration,      setDuration]      = useState(null);
  const [currentIndex,  setCurrentIndex]  = useState(0);

  const generate = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    setCurrentIndex(0); // ← reset dans la fonction async, pas dans useEffect
    try {
      const data = await generateNames(params);
      setResults(data.noms ?? []);
      setDuration(data.duree_ms ?? null);
    } catch (err) {
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
    setCurrentIndex(0);
  }, []);

  return { results, loading, error, duration, currentIndex, setCurrentIndex, generate, clear };
}