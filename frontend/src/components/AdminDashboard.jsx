// src/components/AdminDashboard.jsx
import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { Check, X, ArrowLeft, Loader2, Users } from 'lucide-react';

export default function AdminDashboard({ onGoBack }) {
  const { lang, token } = useApp();
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  // 1. CHARGEMENT DES SUGGESTIONS "PENDING"
  useEffect(() => {
    async function fetchSuggestions() {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/suggestions', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          // On ne garde que les suggestions en attente de modération
          setSuggestions(data.filter(s => s.status === 'pending') || []);
        }
      } catch (error) {
        console.error("Erreur de récupération:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchSuggestions();
  }, [token]);

  // 2. LOGIQUE TRAITEMENT (APPROUVER OU REJETER)
  const handleModerate = async (id, action) => {
    try {
      // action = 'approve' ou 'reject'
      const response = await fetch(`http://127.0.0.1:8000/api/suggestions/${id}/${action}`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        // Simple filter + re-render immédiat de l'état local
        setSuggestions(prev => prev.filter(item => item.id !== id));
        setMessage(action === 'approve' ? 'Suggestion approuvée et intégrée !' : 'Suggestion rejetée.');
        setTimeout(() => setMessage(''), 2500);
      }
    } catch (error) {
      console.error("Erreur lors de la modération:", error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-gray-400 gap-3">
        <Loader2 className="animate-spin text-purple-500" size={32} />
        <p className="text-xs">Chargement du dashboard de modération...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 text-white animate-fade-in">
      
      {/* EN-TÊTE */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-gray-900 pb-6 mb-6">
        <div>
          <h1 className="text-xl font-bold tracking-wide flex items-center gap-2">
            <Users size={20} className="text-purple-500" />
            {lang === 'ar' ? 'لوحة تحكم المشرف' : 'Dashboard Modération Admin'}
          </h1>
          <p className="text-xs text-gray-500 mt-1">
            {lang === 'ar' ? 'راجع واقبل اقتراحات الأسماء من المجتمع.' : 'Validez ou rejetez les propositions de noms soumises par la communauté.'}
          </p>
        </div>
        <button 
          onClick={onGoBack}
          className="flex items-center gap-2 px-4 py-2 bg-[#12141c] hover:bg-gray-900 border border-gray-800 rounded-xl text-xs font-semibold text-gray-400 hover:text-white transition-all active:scale-95"
        >
          <ArrowLeft size={14} />
          <span>{lang === 'ar' ? 'رجوع' : 'Retour à l\'accueil'}</span>
        </button>
      </div>

      {/* TOAST NOTIFICATION FLASH */}
      {message && (
        <div className="mb-4 text-center text-xs font-medium py-2.5 px-4 bg-purple-950/40 text-purple-300 border border-purple-900/40 rounded-xl animate-fade-in">
          {message}
        </div>
      )}

      {/* TABLEAU DES SUGGESTIONS */}
      <div className="bg-[#12141c] border border-gray-900 rounded-2xl overflow-hidden shadow-xl">
        {suggestions.length === 0 ? (
          <div className="text-center py-16 text-gray-600 text-xs space-y-2">
            <p className="text-3xl">☕</p>
            <p>{lang === 'ar' ? 'لا توجد اقتراحات معلقة حالياً.' : 'Aucune suggestion en attente pour le moment. Beau travail !'}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-900 text-gray-500 font-bold text-[10px] tracking-wider uppercase bg-[#161922]/50">
                  <th className="p-4">{lang === 'ar' ? 'الاسم المقترح' : 'Nom Suggéré'}</th>
                  <th className="p-4">{lang === 'ar' ? 'التصنيف' : 'Catégorie'}</th>
                  <th className="p-4">{lang === 'ar' ? 'اللغة' : 'Langue'}</th>
                  <th className="p-4 text-center w-32">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-900/60 text-xs font-medium">
                {suggestions.map((item) => (
                  <tr key={item.id} className="hover:bg-[#161922]/30 transition-all">
                    <td className="p-4 font-bold text-white tracking-wide">{item.nom}</td>
                    <td className="p-4">
                      <span className="bg-gray-900 border border-gray-800 text-gray-400 px-2 py-0.5 rounded-md text-[10px] uppercase font-bold">
                        {item.categorie}
                      </span>
                    </td>
                    <td className="p-4 text-gray-400 uppercase">{item.langue}</td>
                    <td className="p-4 flex items-center justify-center gap-2">
                      {/* BOUTON APPROUVER */}
                      <button
                        onClick={() => handleModerate(item.id, 'approve')}
                        className="w-8 h-8 rounded-lg bg-emerald-950/40 text-emerald-400 border border-emerald-900/30 flex items-center justify-center hover:bg-emerald-600 hover:text-white transition-all active:scale-95"
                        title="Approuver (ajouter au dataset)"
                      >
                        <Check size={14} />
                      </button>
                      {/* BOUTON REJETER */}
                      <button
                        onClick={() => handleModerate(item.id, 'reject')}
                        className="w-8 h-8 rounded-lg bg-red-950/40 text-red-400 border border-red-900/30 flex items-center justify-center hover:bg-red-600 hover:text-white transition-all active:scale-95"
                        title="Rejeter"
                      >
                        <X size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}