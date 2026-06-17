import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import BrandCard from './BrandCard';
import { X, Bookmark, Heart, RotateCcw, ArrowLeft, ArrowRight, Loader2, CreditCard } from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

const SECTEUR_MAP = { Tous: 'GENERAL', Tech: 'TECH', Food: 'FOOD', Luxe: 'LUXE' };

export default function CardsScreen({ config, generationType, onGoBack, onReserveClick }) {
  const { t, lang, addFavorite, token } = useApp();
  const [names, setNames] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [animation, setAnimation] = useState('');
  const [fetchError, setFetchError] = useState('');
  const [modelUsed, setModelUsed] = useState('');

  const isModeB = config.mode === 'B';
  const typeNom = generationType === 'enterprise' ? 'societe' : 'marque';
  const secteur = SECTEUR_MAP[config.style] || 'GENERAL';

  useEffect(() => {
    async function fetchNames() {
      try {
        setLoading(true);
        setFetchError('');
        setNames([]);
        setCurrentIndex(0);
        setModelUsed('');

        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        if (isModeB) {
          const response = await fetch(`${API_BASE}/api/generate-llm`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
              prompt: config.prompt,
              model_key: config.model,
              langue: lang,
              secteur,
              type_nom: typeNom,
              n: 15,
              temperature: 0.8,
            }),
          });

          if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            setFetchError(err.detail || (lang === 'ar' ? 'فشل توليد الأسماء.' : 'Échec de la génération LLM.'));
            return;
          }

          const data = await response.json();
          setNames(data.noms || []);
          setModelUsed(data.model_used || config.modelLabel || config.model);
        } else {
          let promptAEnvoyer = config.prompt;
          if (!config.prompt?.trim()) {
            const typeLabel = generationType === 'enterprise'
              ? (lang === 'ar' ? 'شركة' : 'entreprise')
              : (lang === 'ar' ? 'علامة تجارية' : 'marque');
            let secteurLabel = config.style;
            if (config.style === 'Tous') {
              secteurLabel = lang === 'ar' ? 'عام' : 'moderne';
            }
            promptAEnvoyer = lang === 'ar'
              ? `اسم ${typeLabel} في مجال ${secteurLabel}`
              : `Nom pour une ${typeLabel} dans le secteur ${secteurLabel}`;
          }

          const response = await fetch(`${API_BASE}/api/generate`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
              prompt: promptAEnvoyer,
              secteur: config.style,
              langue: lang,
              n: 30,
              temperature: 0.7,
              top_k: 10,
              seed: null,
            }),
          });

          if (!response.ok) {
            setFetchError(lang === 'ar' ? 'فشل توليد الأسماء.' : 'Échec de la génération.');
            return;
          }

          const data = await response.json();
          setNames(data.noms || []);
        }
      } catch (error) {
        console.error('Erreur backend:', error);
        setFetchError(
          isModeB
            ? (lang === 'ar' ? 'تعذر الاتصال بنموذج LLM. تحقق من Ollama أو مفاتيح API.' : 'Impossible de joindre le LLM. Vérifiez Ollama ou les clés API.')
            : (lang === 'ar' ? 'خطأ في الاتصال بالخادم.' : 'Impossible de joindre le serveur.')
        );
      } finally {
        setLoading(false);
      }
    }
    fetchNames();
  }, [config, lang, generationType, isModeB, typeNom, secteur, token]);

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

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] bg-[#0b0c10] flex flex-col items-center justify-center text-gray-400 gap-4">
        <Loader2 className="animate-spin text-purple-600" size={40} />
        <p className="text-sm font-medium tracking-wide">
          {isModeB
            ? (lang === 'ar' ? 'الذكاء الاصطناعي يولّد أسماء مخصصة...' : 'Le LLM génère vos noms sur mesure...')
            : 'BrandForge calcule vos noms sur mesure...'}
        </p>
        {isModeB && config.modelLabel && (
          <p className="text-[10px] text-purple-400/70 bg-purple-950/30 px-3 py-1 rounded-full border border-purple-900/30">
            {config.modelLabel}
          </p>
        )}
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="min-h-[calc(100vh-4rem)] bg-[#0b0c10] flex flex-col items-center justify-center p-6 text-center text-white">
        <div className="p-8 bg-[#12141c] rounded-3xl border border-gray-900 max-w-sm w-full shadow-2xl flex flex-col items-center gap-4 animate-fade-in">
          <span className="text-4xl">⚠️</span>
          <h3 className="text-xl font-bold tracking-wide">
            {lang === 'ar' ? 'خطأ في التوليد' : 'Erreur de génération'}
          </h3>
          <p className="text-gray-500 text-xs leading-relaxed">{fetchError}</p>
          <button
            onClick={onGoBack}
            className="mt-2 w-full py-3 bg-purple-600 hover:bg-purple-700 font-bold text-white rounded-xl text-xs transition-all active:scale-95"
          >
            {lang === 'ar' ? 'تعديل الإعدادات' : 'Modifier mes paramètres'}
          </button>
        </div>
      </div>
    );
  }

  // ÉCRAN VIDE
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
      
      {/* TOP BARRE : COMPTEUR & MODÈLE LLM */}
      <div className="w-full flex justify-between items-center text-gray-500 font-semibold text-xs">
        <button onClick={onGoBack} className="flex items-center gap-1.5 hover:text-white transition-all p-1">
          {lang === 'ar' ? <ArrowRight size={14} /> : <ArrowLeft size={14} />}
          <span>{remainingCount} {t('remaining')}</span>
        </button>
        <div className="flex items-center gap-2">
          {isModeB && modelUsed && (
            <span className="text-[10px] text-purple-400/80 bg-purple-950/30 px-2 py-0.5 rounded-full border border-purple-900/20">
              LLM · {config.modelLabel || modelUsed}
            </span>
          )}
          <button
            onClick={() => setCurrentIndex(0)}
            className="p-2 bg-[#12141c] hover:text-white rounded-full border border-gray-950 transition-all"
          >
            <RotateCcw size={14} />
          </button>
        </div>
      </div>

      {/* COMPOSANT DE VUE DE CARTE */}
      <div className="flex-1 flex flex-col items-center justify-center my-4 relative w-full gap-4">
        {currentIndex < names.length ? (
          <>
            <BrandCard
              data={currentCard}
              animationClass={animation}
              index={currentIndex}
              config={config}
              isLlm={isModeB}
            />
            
            {/* ⚡ NOUVEAU BOUTON : RÉSERVATION EXPRESS DIRECTEMENT SOUS LA CARTE */}
            <button
              onClick={() => onReserveClick(currentCard.nom)}
              className="w-full max-w-sm py-3 bg-[#12141c] hover:bg-purple-950/20 border border-purple-900/40 text-purple-400 hover:text-purple-300 font-bold rounded-2xl text-xs flex items-center justify-center gap-2 transition-all active:scale-[0.98] shadow-lg"
            >
              <CreditCard size={14} />
              <span>{lang === 'ar' ? 'حجز هذا الاسم (خيار مجاني متاح)' : 'Réserver ce nom (Option gratuite disponible)'}</span>
            </button>
          </>
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
