import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { ArrowLeft, ArrowRight, Sparkles } from 'lucide-react';

export default function PromptScreen({ generationType, onGoBack, onGenerate }) {
  const { t, lang } = useApp();
  const [prompt, setPrompt] = useState('');
  const [selectedStyle, setSelectedStyle] = useState('Tous');
  const [error, setError] = useState(false); // État pour suivre l'erreur du prompt vide

  // Configuration des filtres de styles demandés
  const styles = [
    { id: 'Tous', label: t('styleAll') },
    { id: 'Futuriste', label: t('styleFuturistic') },
    { id: 'Luxe', label: t('styleLuxe') },
    { id: 'Tech', label: t('styleTech') },
    { id: 'Minimal', label: t('styleMinimal') },
  ];

  const BackArrow = lang === 'ar' ? ArrowRight : ArrowLeft;

  const handleSubmit = () => {
    // Validation : Si le prompt est vide ou ne contient que des espaces
    if (!prompt.trim()) {
      setError(true); // Active l'erreur visuelle
      return; // Bloque l'envoi de la génération
    }

    setError(false); // Réinitialise l'erreur si tout est bon
    // On transmet les paramètres à la fonction de génération principale
    onGenerate({ prompt, style: selectedStyle });
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-[#0b0c10] px-6 py-8 flex flex-col justify-between max-w-4xl mx-auto animate-fade-in">
      
      {/* ENTÊTE DE PAGE : RETOUR & TITRE DYNAMIQUE */}
      <div className="w-full flex items-center gap-4 mb-6">
        <button 
          onClick={onGoBack}
          className="p-2 bg-[#12141c] text-gray-400 hover:text-white rounded-full border border-gray-900 transition-all"
        >
          <BackArrow size={20} />
        </button>
        <h2 className="text-xl md:text-2xl font-bold text-white capitalize">
          {generationType === 'entreprise' ? t('btnCompany') : t('btnBrand')}
        </h2>
      </div>

      {/* ZONE CENTRALE : SAISIE & STYLES */}
      <div className="flex-1 flex flex-col gap-8 justify-center">
        
        {/* CHAMP DESCRIPTION */}
        <div className="flex flex-col gap-3">
          <label className="text-gray-500 font-bold text-xs tracking-wider uppercase">
            {lang === 'ar' ? 'صف فكرتك' : 'DÉCRIVEZ VOTRE IDÉE'}
          </label>
          <textarea
            value={prompt}
            onChange={(e) => {
              setPrompt(e.target.value);
              if (e.target.value.trim()) setError(false); // Enlève l'erreur dès que l'utilisateur commence à écrire
            }}
            placeholder={t('placeholder')}
            className={`w-full h-40 p-5 bg-[#12141c] text-white rounded-2xl border transition-all duration-300 text-sm placeholder:text-gray-600 leading-relaxed ${
              error 
                ? 'border-red-500 focus:border-red-500 shadow-lg shadow-red-500/5' 
                : 'border-gray-950 focus:border-purple-600 focus:outline-none'
            } ${lang === 'ar' ? 'text-right' : 'text-left'}`}
          />
          
          {/* MESSAGE D'ERREUR TEXTUEL DYNAMIQUE */}
          {error && (
            <p className={`text-red-500 text-xs font-semibold mt-1 animate-fade-in ${
              lang === 'ar' ? 'text-right' : 'text-left'
            }`}>
              {lang === 'ar' 
                ? '⚠️ الرجاء كتابة وصف لفكرتك أولاً قبل التوليد.' 
                : '⚠️ Veuillez décrire votre idée avant de lancer la génération.'}
            </p>
          )}
        </div>

        {/* COMPOSANT DE SELECTION DU STYLE */}
        <div className="flex flex-col gap-3">
          <label className="text-gray-500 font-bold text-xs tracking-wider uppercase">
            {t('styleTitle')}
          </label>
          <div className="flex flex-wrap gap-2">
            {styles.map((style) => {
              const isSelected = selectedStyle === style.id;
              return (
                <button
                  key={style.id}
                  onClick={() => setSelectedStyle(style.id)}
                  className={`px-5 py-2.5 rounded-full text-xs font-semibold tracking-wide transition-all duration-300 border ${
                    isSelected
                      ? 'bg-purple-600 text-white border-purple-500 shadow-lg shadow-purple-600/20 scale-105'
                      : 'bg-[#12141c] text-gray-400 border-gray-950 hover:border-gray-800 hover:text-gray-200'
                  }`}
                >
                  {style.label}
                </button>
              );
            })}
          </div>
        </div>

      </div>

      {/* BOUTON ACTION MAJEUR : GÉNÉRER */}
      <div className="w-full pt-8">
        <button
          onClick={handleSubmit}
          className="w-full py-4 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-2xl flex items-center justify-center gap-2 shadow-xl shadow-purple-600/10 transition-all duration-300 transform hover:-translate-y-0.5 active:translate-y-0"
        >
          <Sparkles size={18} />
          {t('btnGenerate')}
        </button>
      </div>

    </div>
  );
}