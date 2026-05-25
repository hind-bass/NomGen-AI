import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { ArrowLeft, ArrowRight, Sparkles } from 'lucide-react';

export default function PromptScreen({ generationType, category, onGoBack, onGenerate }) {
  const { t, lang, categories } = useApp();
  const [prompt, setPrompt] = useState('');
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);

  const BackArrow = lang === 'ar' ? ArrowRight : ArrowLeft;

  // Get category info from config
  const getCategoryLabel = () => {
    if (!categories || !generationType || !category) return '';
    const type_config = categories.categories[generationType];
    const sector = type_config.sectors.find(s => s.id === category);
    return sector ? sector[`label_${lang}`] : '';
  };

  const handleSubmit = async () => {
    if (!prompt.trim()) {
      setError(true);
      return;
    }

    setError(false);
    setLoading(true);

    try {
      onGenerate({
        prompt,
        type: generationType,
        category
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-[#0b0c10] px-6 py-8 flex flex-col justify-between max-w-4xl mx-auto animate-fade-in">

      {/* ENTÊTE */}
      <div className="w-full flex items-center gap-4 mb-6">
        <button
          onClick={onGoBack}
          className="p-2 bg-[#12141c] text-gray-400 hover:text-white rounded-full border border-gray-900 transition-all"
        >
          <BackArrow size={20} />
        </button>
        <div className="flex-1">
          <h2 className="text-xl md:text-2xl font-bold text-white capitalize mb-2">
            {generationType === 'entreprise' ? t('btnCompany') : t('btnBrand')}
          </h2>
          <div className="flex items-center gap-2">
            <span className="text-xs bg-purple-600/20 border border-purple-600/50 text-purple-300 px-3 py-1 rounded-full">
              {getCategoryLabel()}
            </span>
          </div>
        </div>
      </div>

      {/* ZONE CENTRALE */}
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
              if (e.target.value.trim()) setError(false);
            }}
            placeholder={t('placeholder')}
            disabled={loading}
            className={`w-full h-40 p-5 bg-[#12141c] text-white rounded-2xl border transition-all duration-300 text-sm placeholder:text-gray-600 leading-relaxed disabled:opacity-60 ${
              error
                ? 'border-red-500 focus:border-red-500 shadow-lg shadow-red-500/5'
                : 'border-gray-950 focus:border-purple-600 focus:outline-none'
            } ${lang === 'ar' ? 'text-right' : 'text-left'}`}
          />

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

      </div>

      {/* BOUTON ACTION */}
      <div className="w-full pt-8">
        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full py-4 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white font-bold rounded-2xl flex items-center justify-center gap-2 shadow-xl shadow-purple-600/10 transition-all duration-300 transform hover:-translate-y-0.5 active:translate-y-0 disabled:cursor-not-allowed"
        >
          <Sparkles size={18} />
          {loading ? (lang === 'ar' ? 'جاري التوليد...' : 'Génération en cours...') : t('btnGenerate')}
        </button>
      </div>

    </div>
  );
}