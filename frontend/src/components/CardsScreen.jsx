import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import BrandCard from './BrandCard';
import AppIcon from './AppIcon';
import { API_BASE } from '../config/api';
import { X, Bookmark, Heart, RotateCcw, ArrowLeft, ArrowRight, Loader2, CreditCard } from 'lucide-react';

const SECTEUR_MAP = { Tous: 'GENERAL', Tech: 'TECH', Food: 'FOOD', Luxe: 'LUXE' };

export default function CardsScreen({ config, generationType, onGoBack, onReserveClick }) {
  const { t, lang, addFavorite, token } = useApp();
  const [names, setNames] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [animation, setAnimation] = useState('');
  const [fetchError, setFetchError] = useState('');
  const [modelUsed, setModelUsed] = useState('');
  const [dragX, setDragX] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const dragStartX = useRef(0);
  const cardRef = useRef(null);

  const SWIPE_THRESHOLD = 80;

  const sendFeedback = useCallback(async (generationId, voteType) => {
    if (!generationId) return;
    try {
      await fetch(`${API_BASE}/feedback/${voteType}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ generation_id: generationId }),
      });
    } catch (e) {
      console.error('Erreur feedback:', e);
    }
  }, [token]);

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
              n: config.model?.includes('nomgen') ? 8 : 10,
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

  // Logique like / dislike / favori (boutons + swipe)
  const handleAction = useCallback((type) => {
    if (currentIndex >= names.length) return;

    const card = names[currentIndex];
    const cardWithStyle = {
      ...card,
      style: card?.style || config.style,
      secteur: card?.secteur || secteur,
      langue: card?.langue || lang,
      generation_id: card?.generation_id,
    };

    if (type === 'like') {
      sendFeedback(card?.generation_id, 'like');
      addFavorite(cardWithStyle);
    }
    if (type === 'save') {
      addFavorite(cardWithStyle);
    }
    if (type === 'dislike') {
      sendFeedback(card?.generation_id, 'dislike');
    }

    if (type === 'pass' || type === 'dislike') setAnimation('animate-swipe-left');
    if (type === 'like') setAnimation('animate-swipe-right');
    if (type === 'save') setAnimation('animate-bounce-up');

    setDragX(0);
    setIsDragging(false);

    setTimeout(() => {
      setCurrentIndex((prev) => prev + 1);
      setAnimation('');
    }, 450);
  }, [currentIndex, names, config.style, secteur, lang, addFavorite, sendFeedback]);

  const onPointerDown = (e) => {
    if (currentIndex >= names.length || animation) return;
    dragStartX.current = e.clientX;
    setIsDragging(true);
    e.currentTarget.setPointerCapture(e.pointerId);
  };

  const onPointerMove = (e) => {
    if (!isDragging || animation) return;
    setDragX(e.clientX - dragStartX.current);
  };

  const onPointerUp = (e) => {
    if (!isDragging) return;
    try { e.currentTarget.releasePointerCapture(e.pointerId); } catch { /* ignore */ }
    setIsDragging(false);

    const delta = e.clientX - dragStartX.current;
    if (delta > SWIPE_THRESHOLD) {
      handleAction('like');
    } else if (delta < -SWIPE_THRESHOLD) {
      handleAction('dislike');
    } else {
      setDragX(0);
    }
  };

  const onPointerCancel = () => {
    setIsDragging(false);
    setDragX(0);
  };

  const cardTransform = isDragging && !animation
    ? `translateX(${dragX}px) rotate(${dragX * 0.06}deg)`
    : undefined;

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
        {isModeB && config.model?.includes('nomgen') && (
          <p className="text-[10px] text-gray-500 max-w-xs text-center px-4">
            {lang === 'ar'
              ? 'النموذج المخصص قد يستغرق 2–5 دقائق في المرة الأولى. لا تغلق الصفحة.'
              : 'Modèle fine-tuné : 2–5 min la 1ère fois (chargement Ollama). Ne fermez pas la page.'}
          </p>
        )}
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="min-h-[calc(100vh-4rem)] bg-[#0b0c10] flex flex-col items-center justify-center p-6 text-center text-white">
        <div className="p-8 bg-[#12141c] rounded-3xl border border-gray-900 max-w-sm w-full shadow-2xl flex flex-col items-center gap-4 animate-fade-in">
          <AppIcon name="warning" size={48} alt="" className="mb-1" />
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
          <AppIcon name="thinking" size={48} alt="" className="mb-1" />
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
    <div className="min-h-[calc(100vh-4rem)] bg-[#0b0c10] px-4 sm:px-6 py-4 flex flex-col justify-between max-w-xl mx-auto animate-fade-in">
      
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

      {/* CARTE SWIPABLE */}
      <div className="flex-1 flex flex-col items-center justify-center my-4 relative w-full gap-4">
        {currentIndex < names.length ? (
          <>
            <div
              ref={cardRef}
              className="relative w-full max-w-md touch-pan-y select-none cursor-grab active:cursor-grabbing"
              style={{ transform: cardTransform, transition: isDragging ? 'none' : 'transform 0.3s ease' }}
              onPointerDown={onPointerDown}
              onPointerMove={onPointerMove}
              onPointerUp={onPointerUp}
              onPointerCancel={onPointerCancel}
            >
              {/* Indicateurs swipe */}
              {dragX > 40 && (
                <div className="absolute top-8 left-8 z-20 px-4 py-2 border-4 border-emerald-400 text-emerald-400 font-black text-lg rounded-xl rotate-[-12deg] bg-emerald-950/40 pointer-events-none">
                  LIKE
                </div>
              )}
              {dragX < -40 && (
                <div className="absolute top-8 right-8 z-20 px-4 py-2 border-4 border-red-400 text-red-400 font-black text-lg rounded-xl rotate-[12deg] bg-red-950/40 pointer-events-none">
                  NOPE
                </div>
              )}

              <BrandCard
                data={currentCard}
                animationClass={animation}
                index={currentIndex}
                config={config}
                isLlm={isModeB}
              />
            </div>

            <button
              onClick={() => onReserveClick(currentCard.nom)}
              className="w-full max-w-md py-3 bg-[#12141c] hover:bg-purple-950/20 border border-purple-900/40 text-purple-400 hover:text-purple-300 font-bold rounded-2xl text-xs flex items-center justify-center gap-2 transition-all active:scale-[0.98] shadow-lg"
            >
              <CreditCard size={14} />
              <span>{lang === 'ar' ? 'حجز هذا الاسم (خيار مجاني متاح)' : 'Réserver ce nom (Option gratuite disponible)'}</span>
            </button>
          </>
        ) : (
          <div className="text-center p-8 bg-[#12141c] rounded-3xl border border-gray-950 w-full max-w-sm aspect-[3/4] flex flex-col justify-center items-center gap-2">
            <AppIcon name="party" size={40} alt="" />
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
          onClick={() => handleAction('dislike')}
          className="w-14 h-14 bg-[#12141c] text-red-500 border border-gray-950 hover:border-red-900/50 rounded-full flex items-center justify-center shadow-lg transition-all active:scale-95 disabled:opacity-20"
          title={lang === 'ar' ? 'رفض' : 'Dislike'}
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
