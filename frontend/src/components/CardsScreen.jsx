import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import BrandCard from './BrandCard';
import { X, Bookmark, Heart, RotateCcw, ArrowLeft, ArrowRight, Loader2 } from 'lucide-react';

export default function CardsScreen({ config, generationType, onGoBack }) {
  const { t, lang, addFavorite } = useApp();
  const [names, setNames] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [animation, setAnimation] = useState('');

  // 1. APPEL À VOTRE SERVEUR FASTAPI DYNAMIQUE
  useEffect(() => {
    async function fetchNames() {
      try {
        setLoading(true);
        // ⚡ RÉPARATION CRITIQUE : Réinitialisation systématique de la liste et de l'index
        // Cela force le composant à se vider avant de recevoir la réponse (cohérente ou non) de FastAPI
        setNames([]);
        setCurrentIndex(0);

        const response = await fetch('http://127.0.0.1:8000/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: config.prompt,
            secteur: config.style, 
            langue: lang, 
            n: 30,
            temperature: 0.7,
            top_k: 10,
            seed: null
          })
        });
        const data = await response.json();
        setNames(data.noms || []);
      } catch (error) {
        console.error("Erreur backend:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchNames();
  }, [config, lang, generationType]);

  const currentCard = names[currentIndex];
  const remainingCount = names.length - currentIndex;

  // 2. LOGIQUE DU SWIPE ANIMÉ
  const handleAction = (type) => {
    if (currentIndex >= names.length) return;

    if (type === 'like' || type === 'save') {
      const cardWithStyle = {
        ...currentCard,
        style: currentCard?.style || config.style,
        secteur: currentCard?.secteur || config.style
      };
      addFavorite(cardWithStyle);
    }

    if (type === 'pass') setAnimation('animate-swipe-left');
    if (type === 'like') setAnimation('animate-swipe-right');
    if (type === 'save') setAnimation('animate-bounce-up');

    setTimeout(() => {
      setCurrentIndex((prev) => prev + 1);
      setAnimation('');
    }, 450);
  };

  // ÉCRAN DE CHARGEMENT SQUELETTE
  if (loading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] bg-[#0b0c10] flex flex-col items-center justify-center text-gray-400 gap-4">
        <Loader2 className="animate-spin text-purple-600" size={40} />
        <p className="text-sm font-medium tracking-wide">BrandForge calcule vos noms sur mesure...</p>
      </div>
    );
  }

  // ⚡ ÉCRAN DE GESTION DU TEXTE INCOHÉRENT (Fonctionne à chaque itération grâce au nettoyage d'état)
  if (!loading && names.length === 0) {
    return (
      <div className="min-h-[calc(100vh-4rem)] bg-[#0b0c10] flex flex-col items-center justify-center p-6 text-center text-white">
        <div className="p-8 bg-[#12141c] rounded-3xl border border-gray-900 max-w-sm w-full shadow-2xl flex flex-col items-center gap-4 animate-fade-in">
          <span className="text-4xl">🤔</span>
          <h3 className="text-xl font-bold tracking-wide">
            {lang === 'ar' ? 'وصف غير مفهوم' : 'Concept non reconnu'}
          </h3>
          <p className="text-gray-500 text-xs leading-relaxed">
            {lang === 'ar' 
              ? 'يبدو أن الوصف الذي أدخلته غير واضح أو عشوائي. يرجى كتابة كلمات رئيسية مفهومة (مثال: شركة تقنية حديثة، مشروع فاخر).' 
              : 'Votre description semble incohérente ou contient du texte aléatoire. Essayez d\'ajouter des mots-clés clairs (ex: "startup tech moderne", "luxe durable").'}
          </p>
          <button 
            onClick={onGoBack} 
            className="mt-2 w-full py-3 bg-purple-600 hover:bg-purple-700 font-bold text-white rounded-xl text-xs transition-all active:scale-95 shadow-lg shadow-purple-950/20"
          >
            {lang === 'ar' ? 'تعديل الوصف ×' : 'Modifier mon prompt'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-[#0b0c10] px-6 py-4 flex flex-col justify-between max-w-lg mx-auto animate-fade-in">
      
      {/* TOP BARRE : COMPTEUR & RE-GÉNÉRER */}
      <div className="w-full flex justify-between items-center text-gray-500 font-semibold text-xs">
        <button onClick={onGoBack} className="flex items-center gap-1.5 hover:text-white transition-all p-1">
          {lang === 'ar' ? <ArrowRight size={14} /> : <ArrowLeft size={14} />}
          <span>{remainingCount} {t('remaining')}</span>
        </button>
        <button 
          onClick={() => { setCurrentIndex(0); }} 
          className="p-2 bg-[#12141c] hover:text-white rounded-full border border-gray-950 transition-all"
        >
          <RotateCcw size={14} />
        </button>
      </div>

      {/* COMPOSANT DE VUE DE CARTE */}
      <div className="flex-1 flex items-center justify-center my-6 relative w-full">
        {currentIndex < names.length ? (
          <BrandCard 
            data={currentCard} 
            animationClass={animation} 
            index={currentIndex} 
            config={config} 
          />
        ) : (
          <div className="text-center p-8 bg-[#12141c] rounded-3xl border border-gray-950 w-full max-w-sm aspect-[3/4] flex flex-col justify-center items-center gap-2">
            <span className="text-3xl">🎉</span>
            <h3 className="text-white font-bold mt-2">Fin de la sélection</h3>
            <p className="text-gray-500 text-xs max-w-[200px] mx-auto">Modifiez votre prompt pour explorer d'autres déclinaisons.</p>
          </div>
        )}
      </div>

      {/* LÉGENDES INDICATIVES */}
      {currentIndex < names.length && (
        <div className="text-center text-gray-600 text-[11px] font-medium tracking-wide flex justify-center gap-8 mb-4">
          <span className="flex items-center gap-1.5"><X size={12} className="text-red-500/50" /> {t('swipeLeft')}</span>
          <span className="flex items-center gap-1.5"><Heart size={12} className="text-emerald-500/50" /> {t('swipeRight')}</span>
        </div>
      )}

      {/* BARRE D'ACTIONS INFÉRIEURE */}
      <div className="w-full flex justify-center items-center gap-5 pb-6">
        <button
          disabled={currentIndex >= names.length}
          onClick={() => handleAction('pass')}
          className="w-14 h-14 bg-[#12141c] text-red-500 border border-gray-950 hover:border-red-900/50 rounded-full flex items-center justify-center shadow-lg transition-all active:scale-95 disabled:opacity-20"
        >
          <X size={22} />
        </button>

        <button
          disabled={currentIndex >= names.length}
          onClick={() => handleAction('save')}
          className="w-12 h-12 bg-[#12141c] text-purple-400 border border-gray-950 hover:border-purple-900/50 rounded-full flex items-center justify-center shadow-lg transition-all active:scale-95 disabled:opacity-20"
        >
          <Bookmark size={18} />
        </button>

        <button
          disabled={currentIndex >= names.length}
          onClick={() => handleAction('like')}
          className="w-14 h-14 bg-[#12141c] text-emerald-400 border border-gray-950 hover:border-emerald-900/50 rounded-full flex items-center justify-center shadow-lg transition-all active:scale-95 disabled:opacity-20"
        >
          <Heart size={22} />
        </button>
      </div>

    </div>
  );
}
