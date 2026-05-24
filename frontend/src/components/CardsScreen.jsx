import { useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { useGenerator } from '../hooks/useGenerator';
import BrandCard from './BrandCard';
import { X, Bookmark, Heart, RotateCcw, ArrowLeft, ArrowRight, Loader2, AlertTriangle } from 'lucide-react';

export default function CardsScreen({ config, generationType, onGoBack }) {
  const { t, lang, addFavorite } = useApp();

  // currentIndex est maintenant géré dans useGenerator
  const { results, loading, error, currentIndex, setCurrentIndex, generate } = useGenerator();

  // ── Déclenchement automatique — PAS de setState synchrone ici ────────────
  useEffect(() => {
    generate({
      prompt:         config.prompt,
      style:          config.style,
      generationType: generationType,
      langue:         lang,
      n:              30,
      temperature:    0.7,
      topK:           10,
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config, lang, generationType]);

  const currentCard    = results[currentIndex];
  const remainingCount = results.length - currentIndex;

  // ── Gestion du swipe avec animation ──────────────────────────────────────
  const handleAction = (type) => {
    if (currentIndex >= results.length) return;

    if (type === 'like' || type === 'save') {
      const cardWithMeta = {
        ...currentCard,
        style:   currentCard?.style   || config.style,
        secteur: currentCard?.secteur || config.style,
      };
      addFavorite(cardWithMeta);
    }

    const animMap = { pass: 'animate-swipe-left', like: 'animate-swipe-right', save: 'animate-bounce-up' };

    // Applique l'animation via la carte directement
    setTimeout(() => {
      setCurrentIndex((prev) => prev + 1);
    }, 450);

    // On passe l'animation à la carte via une ref locale (voir BrandCard)
    const card = document.querySelector('.brand-card-active');
    if (card && animMap[type]) {
      card.classList.add(animMap[type]);
    }
  };

  // ── Régénérer ─────────────────────────────────────────────────────────────
  const handleRegen = () => {
    generate({
      prompt:         config.prompt,
      style:          config.style,
      generationType: generationType,
      langue:         lang,
      n:              30,
      temperature:    0.9,
      topK:           15,
    });
  };

  // ── Écran de chargement ───────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] bg-[#0b0c10] flex flex-col items-center justify-center text-gray-400 gap-4">
        <Loader2 className="animate-spin text-purple-600" size={40} />
        <p className="text-sm font-medium tracking-wide">
          {lang === 'ar' ? 'جارٍ توليد الأسماء...' : 'Génération en cours…'}
        </p>
      </div>
    );
  }

  // ── Écran d'erreur réseau ─────────────────────────────────────────────────
  if (error) {
    return (
      <div className="min-h-[calc(100vh-4rem)] bg-[#0b0c10] flex flex-col items-center justify-center p-6 text-center text-white">
        <div className="p-8 bg-[#12141c] rounded-3xl border border-red-900/40 max-w-sm w-full shadow-2xl flex flex-col items-center gap-4 animate-fade-in">
          <AlertTriangle className="text-red-400" size={36} />
          <h3 className="text-xl font-bold">
            {lang === 'ar' ? 'خطأ في الاتصال' : 'Erreur de connexion'}
          </h3>
          <p className="text-gray-500 text-xs leading-relaxed">{error}</p>
          <button
            onClick={handleRegen}
            className="mt-2 w-full py-3 bg-purple-600 hover:bg-purple-700 font-bold text-white rounded-xl text-xs transition-all active:scale-95"
          >
            {lang === 'ar' ? 'إعادة المحاولة' : 'Réessayer'}
          </button>
          <button onClick={onGoBack} className="text-xs text-gray-600 hover:text-gray-400 transition-all">
            {lang === 'ar' ? 'العودة' : 'Retour au prompt'}
          </button>
        </div>
      </div>
    );
  }

  // ── Écran liste vide ──────────────────────────────────────────────────────
  if (!loading && results.length === 0) {
    return (
      <div className="min-h-[calc(100vh-4rem)] bg-[#0b0c10] flex flex-col items-center justify-center p-6 text-center text-white">
        <div className="p-8 bg-[#12141c] rounded-3xl border border-gray-900 max-w-sm w-full shadow-2xl flex flex-col items-center gap-4 animate-fade-in">
          <span className="text-4xl">🤔</span>
          <h3 className="text-xl font-bold tracking-wide">
            {lang === 'ar' ? 'وصف غير مفهوم' : 'Concept non reconnu'}
          </h3>
          <p className="text-gray-500 text-xs leading-relaxed">
            {lang === 'ar'
              ? 'يبدو أن الوصف الذي أدخلته غير واضح. يرجى كتابة كلمات رئيسية مفهومة.'
              : 'Votre description semble trop vague. Essayez : "startup tech moderne", "marque luxe durable".'}
          </p>
          <button
            onClick={onGoBack}
            className="mt-2 w-full py-3 bg-purple-600 hover:bg-purple-700 font-bold text-white rounded-xl text-xs transition-all active:scale-95"
          >
            {lang === 'ar' ? 'تعديل الوصف' : 'Modifier mon prompt'}
          </button>
        </div>
      </div>
    );
  }

  // ── Vue principale : swipe cards ──────────────────────────────────────────
  return (
    <div className="min-h-[calc(100vh-4rem)] bg-[#0b0c10] px-6 py-4 flex flex-col justify-between max-w-lg mx-auto animate-fade-in">

      {/* BARRE SUPÉRIEURE */}
      <div className="w-full flex justify-between items-center text-gray-500 font-semibold text-xs">
        <button onClick={onGoBack} className="flex items-center gap-1.5 hover:text-white transition-all p-1">
          {lang === 'ar' ? <ArrowRight size={14} /> : <ArrowLeft size={14} />}
          <span>{remainingCount} {t('remaining')}</span>
        </button>
        <button
          onClick={handleRegen}
          className="p-2 bg-[#12141c] hover:text-white rounded-full border border-gray-950 transition-all"
          title={lang === 'ar' ? 'إعادة التوليد' : 'Regénérer'}
        >
          <RotateCcw size={14} />
        </button>
      </div>

      {/* CARTE ACTIVE */}
      <div className="flex-1 flex items-center justify-center my-6 relative w-full">
        {currentIndex < results.length ? (
          <BrandCard
            data={currentCard}
            animationClass=""
            index={currentIndex}
            config={config}
          />
        ) : (
          <div className="text-center p-8 bg-[#12141c] rounded-3xl border border-gray-950 w-full max-w-sm aspect-[3/4] flex flex-col justify-center items-center gap-3">
            <span className="text-3xl">✅</span>
            <h3 className="text-white font-bold mt-2">
              {lang === 'ar' ? 'انتهت القائمة' : 'Fin de la sélection'}
            </h3>
            <p className="text-gray-500 text-xs max-w-[200px] mx-auto">
              {lang === 'ar'
                ? 'يمكنك إعادة التوليد أو تعديل الوصف.'
                : "Regénérez ou modifiez votre prompt pour explorer d'autres noms."}
            </p>
            <button
              onClick={handleRegen}
              className="mt-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold rounded-xl transition-all"
            >
              {lang === 'ar' ? 'إعادة التوليد' : 'Regénérer'}
            </button>
          </div>
        )}
      </div>

      {/* LÉGENDES */}
      {currentIndex < results.length && (
        <div className="text-center text-gray-600 text-[11px] font-medium tracking-wide flex justify-center gap-8 mb-4">
          <span className="flex items-center gap-1.5">
            <X size={12} className="text-red-500/50" /> {t('swipeLeft')}
          </span>
          <span className="flex items-center gap-1.5">
            <Heart size={12} className="text-emerald-500/50" /> {t('swipeRight')}
          </span>
        </div>
      )}

      {/* BOUTONS D'ACTION */}
      <div className="w-full flex justify-center items-center gap-5 pb-6">
        <button
          disabled={currentIndex >= results.length}
          onClick={() => handleAction('pass')}
          className="w-14 h-14 bg-[#12141c] text-red-500 border border-gray-950 hover:border-red-900/50 rounded-full flex items-center justify-center shadow-lg transition-all active:scale-95 disabled:opacity-20"
          aria-label="Passer"
        >
          <X size={22} />
        </button>
        <button
          disabled={currentIndex >= results.length}
          onClick={() => handleAction('save')}
          className="w-12 h-12 bg-[#12141c] text-purple-400 border border-gray-950 hover:border-purple-900/50 rounded-full flex items-center justify-center shadow-lg transition-all active:scale-95 disabled:opacity-20"
          aria-label="Sauvegarder"
        >
          <Bookmark size={18} />
        </button>
        <button
          disabled={currentIndex >= results.length}
          onClick={() => handleAction('like')}
          className="w-14 h-14 bg-[#12141c] text-emerald-400 border border-gray-950 hover:border-emerald-900/50 rounded-full flex items-center justify-center shadow-lg transition-all active:scale-95 disabled:opacity-20"
          aria-label="Aimer"
        >
          <Heart size={22} />
        </button>
      </div>

    </div>
  );
}