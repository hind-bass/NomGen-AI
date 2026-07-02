import React, { useState } from 'react';
import Navbar from './components/Navbar';
import MainSelection from './components/MainSelection';
import PromptScreen from './components/PromptScreen';
import CardsScreen from './components/CardsScreen';
import AuthScreen from './components/AuthScreen';
import AdminDashboard from './components/AdminDashboard'; 
import HistoryPanel from './components/HistoryPanel';
import { useApp } from './context/AppContext'; 
import { Trash2, CreditCard, Send, CheckCircle } from 'lucide-react';
import { validateBillingForm, formatCardNumber, formatExpiry } from './utils/paymentValidation';
import AppIcon, { PlanFeature } from './components/AppIcon';
import { API_BASE } from './config/api';

function parseApiError(data, fallback) {
  if (!data) return fallback;
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg || item.message).filter(Boolean).join(' ') || fallback;
  }
  if (typeof data.message === 'string') return data.message;
  return fallback;
}

export default function App() {
  const [screen, setScreen] = useState('home'); // 'home', 'prompt', 'cards', 'admin'
  const [generationType, setGenerationType] = useState(null);
  const [favoritesOpen, setFavoritesOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [config, setConfig] = useState({ prompt: '', style: 'Tous' });

  // ⚡ ÉTATS MODALE SUGGESTION (NAVBAR) - Enrichi avec type et secteur demandés
  const [navbarSuggestionOpen, setNavbarSuggestionOpen] = useState(false);
  const [formData, setFormData] = useState({ nom: '', type: 'marque', secteur: 'Tech' });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitMessage, setSubmitMessage] = useState('');

  // ⚡ ÉTATS MODALE INTERNE DE TARIFS & PAIEMENT (3 OPTIONS)
  const [paymentModalOpen, setPaymentModalOpen] = useState(false);
  const [paymentStep, setPaymentStep] = useState(1); // 1: Choix du Forfait (3 colonnes), 2: Formulaire CB
  const [selectedNameForBooking, setSelectedNameForBooking] = useState('');
  const [selectedPlan, setSelectedPlan] = useState(''); // 'free', 'pro' ou 'max'
  const [billingData, setBillingData] = useState({ nom: '', prenom: '', email: '', carte: '', expiry: '', cvc: '' });
  const [isPaying, setIsPaying] = useState(false);
  const [paymentMessage, setPaymentMessage] = useState('');
  const [paymentMessageType, setPaymentMessageType] = useState(''); // 'success' | 'error'
  const [favoriteToDelete, setFavoriteToDelete] = useState(null);

  const { lang, t, token, user, userRole, loginUser, favorites, removeFavorite, exportToCSV, exportToJSON } = useApp();

  const handleAuthSuccess = (userData, receivedToken) => {
    loginUser(userData, receivedToken);
    // Redirection selon le rôle retourné par l'API / JWT
    if (userData?.role === 'admin') {
      setScreen('admin');
    } else {
      setScreen('home');
    }
  };

  const handleSelectMode = (type) => {
    setGenerationType(type);
    setScreen('prompt');
  };

  const handleGenerate = (data) => {
    setConfig(data);
    setScreen('cards'); 
  };

  const SECTEUR_TO_STYLE = { GENERAL: 'Tous', TECH: 'Tech', FOOD: 'Food', LUXE: 'Luxe' };

  const handleRelaunchFromHistory = (item) => {
    setHistoryOpen(false);
    setGenerationType('brand');
    const nextConfig = {
      prompt: item.prompt,
      style: SECTEUR_TO_STYLE[item.secteur] || item.secteur || 'Tous',
      mode: item.mode === 'B' ? 'B' : 'A',
      model: config.model,
      modelLabel: config.modelLabel,
    };
    setConfig(nextConfig);
    setScreen(item.mode === 'B' ? 'prompt' : 'cards');
  };

  // ⚡ OUVERTURE DU WORKFLOW DE RÉSERVATION
  const handleOpenPaymentWorkflow = (name) => {
    setSelectedNameForBooking(name);
    setBillingData({
      nom: user?.nom?.split(' ')[1] || '',
      prenom: user?.nom?.split(' ')[0] || '',
      email: user?.email || '',
      carte: '',
      expiry: '',
      cvc: ''
    });
    setPaymentStep(1); 
    setPaymentMessage('');
    setPaymentMessageType('');
    setPaymentModalOpen(true);
  };

  // Sélection d'un forfait
  const handleSelectPlan = (plan) => {
    setSelectedPlan(plan);
    if (plan === 'free') {
      handleProcessReservation(plan, { nom: user?.nom?.split(' ')[1] || '', prenom: user?.nom?.split(' ')[0] || '', email: user?.email || '', carte: 'GRATUIT' });
    } else {
      setPaymentStep(2); // Formulaire CB pour Pro et Max
    }
  };

  const handleProcessReservation = async (plan, dataToSend) => {
    const validationError = validateBillingForm(dataToSend, plan, lang);
    if (validationError) {
      setPaymentMessage(validationError);
      setPaymentMessageType('error');
      return;
    }

    try {
      setIsPaying(true);
      setPaymentMessage('');
      setPaymentMessageType('');

      const response = await fetch('http://127.0.0.1:8000/api/reservations/pay', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          nom_propose: selectedNameForBooking,
          forfait: plan,
          client_nom: dataToSend.nom.trim(),
          client_prenom: dataToSend.prenom.trim(),
          client_email: dataToSend.email.trim(),
          numero_carte: plan === 'free' ? '' : dataToSend.carte.replace(/\D/g, ''),
          card_expiry: plan === 'free' ? '' : dataToSend.expiry.trim(),
          card_cvc: plan === 'free' ? '' : dataToSend.cvc.trim(),
          langue: lang,
          secteur: 'GENERAL',
        })
      });

      if (response.ok) {
        setPaymentMessage(
          lang === 'ar'
            ? 'تم إرسال طلب الحجز إلى المسؤول!'
            : 'Demande envoyée à l\'administrateur pour validation !'
        );
        setPaymentMessageType('success');
        setTimeout(() => {
          setPaymentModalOpen(false);
          setPaymentStep(1);
          setPaymentMessage('');
          setPaymentMessageType('');
        }, 3000);
      } else {
        const err = await response.json().catch(() => ({}));
        setPaymentMessage(
          typeof err.detail === 'string'
            ? err.detail
            : (lang === 'ar' ? 'حدث خطأ أثناء المعالجة.' : 'Erreur lors du traitement de la réservation.')
        );
        setPaymentMessageType('error');
      }
    } catch (error) {
      console.error(error);
      setPaymentMessage(lang === 'ar' ? 'خطأ في الاتصال بالخادم.' : 'Impossible de joindre le serveur.');
      setPaymentMessageType('error');
    } finally {
      setIsPaying(false);
    }
  };

  const handleProcessPaymentSubmit = (e) => {
    e.preventDefault();
    const validationError = validateBillingForm(billingData, selectedPlan, lang);
    if (validationError) {
      setPaymentMessage(validationError);
      setPaymentMessageType('error');
      return;
    }
    handleProcessReservation(selectedPlan, billingData);
  };

  // ⚡ SOUMISSION SUGGESTION NAVBAR
  const SECTEUR_SUGGESTION_MAP = {
    Tech: 'tech',
    Food: 'food',
    General: 'general',
    Luxe: 'luxe',
    Tous: 'general',
  };
  const TYPE_SUGGESTION_MAP = {
    marque: 'marque',
    entreprise: 'societe',
  };

  const handleFormSuggestionSubmit = async (e) => {
    e.preventDefault();
    if (!formData.nom.trim()) return;

    if (!token) {
      setSubmitMessage(
        lang === 'ar'
          ? 'يجب تسجيل الدخول لإرسال اقتراح.'
          : 'Connectez-vous pour proposer un nom.'
      );
      return;
    }

    try {
      setIsSubmitting(true);
      setSubmitMessage('');

      const response = await fetch(`${API_BASE}/api/suggestions/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          nom: formData.nom.trim(),
          categorie: SECTEUR_SUGGESTION_MAP[formData.secteur] || formData.secteur.toLowerCase(),
          type_nom: TYPE_SUGGESTION_MAP[formData.type] || formData.type,
          langue: lang === 'ar' ? 'ar' : 'fr',
        }),
      });

      const data = await response.json().catch(() => ({}));
      const fallbackError = lang === 'ar' ? 'حدث خطأ أثناء الإرسال.' : 'Erreur lors de l\'envoi.';

      if (response.ok) {
        setSubmitMessage(
          lang === 'ar'
            ? 'تم إرسال اقتراحك! في انتظار موافقة المسؤول.'
            : 'Envoyé avec succès ! En attente de validation par l\'administrateur.'
        );
        setFormData({ nom: '', type: 'marque', secteur: 'Tech' });
        setTimeout(() => {
          setNavbarSuggestionOpen(false);
          setSubmitMessage('');
        }, 2500);
      } else {
        setSubmitMessage(parseApiError(data, fallbackError));
      }
    } catch (error) {
      console.error(error);
      setSubmitMessage(lang === 'ar' ? 'خطأ في الاتصال بالخادم.' : 'Impossible de joindre le serveur.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRemoveFavorite = (fav) => {
    setFavoriteToDelete(fav);
  };

  const confirmRemoveFavorite = async () => {
    if (!favoriteToDelete) return;
    await removeFavorite(favoriteToDelete.id || favoriteToDelete.nom);
    setFavoriteToDelete(null);
  };

  if (!token) {
    return <AuthScreen onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <div className="min-h-screen bg-[#0b0c10] font-sans antialiased flex flex-col">
      
      <Navbar 
        onOpenFavorites={() => { setHistoryOpen(false); setFavoritesOpen(true); }} 
        onOpenHistory={() => { setFavoritesOpen(false); setHistoryOpen(true); }}
        onOpenSuggestion={() => setNavbarSuggestionOpen(true)} 
      />

      {userRole === 'admin' && (
        <div className="bg-purple-900/40 border-b border-purple-800 px-6 py-2 flex justify-between items-center text-xs text-purple-200">
          <span className="flex items-center gap-2">
            <AppIcon name="shield" size={16} alt="Admin" />
            Mode Administrateur Activé
          </span>
          <button 
            onClick={() => setScreen(screen === 'admin' ? 'home' : 'admin')}
            className="bg-purple-700 hover:bg-purple-600 font-bold px-3 py-1 rounded text-white transition-all"
          >
            {screen === 'admin' ? 'Quitter le Dashboard' : 'Ouvrir l\'Espace Admin'}
          </button>
        </div>
      )}

      <main className="flex-1">
        {screen === 'home' && <MainSelection onSelectMode={handleSelectMode} />}
        {screen === 'prompt' && (
          <div className="animate-fade-in">
            <PromptScreen
              generationType={generationType}
              onGoBack={() => setScreen('home')}
              onGenerate={handleGenerate}
              initialConfig={config.prompt ? config : null}
            />
          </div>
        )}
        {screen === 'cards' && (
          <CardsScreen config={config} generationType={generationType} onGoBack={() => setScreen('prompt')} onReserveClick={handleOpenPaymentWorkflow} />
        )}
        {screen === 'admin' && userRole === 'admin' && <AdminDashboard onGoBack={() => setScreen('home')} />}
      </main>

      {/* MODAL FAVORIS */}
      {favoritesOpen && (
        <div className={`fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex ${lang === 'ar' ? 'justify-start' : 'justify-end'} animate-fade-in`}>
          <div className="flex-1" onClick={() => setFavoritesOpen(false)} />
          <div className="w-full max-w-lg bg-[#12141c] h-full p-5 sm:p-6 text-white shadow-2xl flex flex-col h-full min-h-0" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
            <div className="flex justify-between items-center border-b border-gray-900 pb-3 mb-4 shrink-0">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <AppIcon name="heart" size={20} alt="Favoris" />
                {t('favTitle')}
              </h2>
              <button onClick={() => setFavoritesOpen(false)} className="text-xs bg-[#1f2833] hover:bg-purple-600 px-3 py-1.5 rounded-full text-gray-300">
                {lang === 'ar' ? 'إغلاق ×' : 'Fermer ×'}
              </button>
            </div>

            <div className="flex-1 min-h-0 overflow-y-auto space-y-2.5 pr-1">
              {favorites.length === 0 ? (
                <div className="text-center py-10 text-gray-600 text-sm flex flex-col items-center gap-3">
                  <AppIcon name="folderEmpty" size={36} alt="" />
                  {t('noFav')}
                </div>
              ) : (
                favorites.map((fav, i) => (
                  <div key={fav.id || i} className="flex flex-col gap-2.5 p-3.5 bg-[#1f2833]/40 border border-gray-900 rounded-xl group">
                    <div className="flex justify-between items-center gap-2">
                      <h4 className="text-white font-bold text-sm truncate">{fav.nom}</h4>
                      {fav.score != null && fav.score !== '' && (
                        <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/30 px-2 py-0.5 rounded-full shrink-0">{fav.score}/100</span>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={() => handleRemoveFavorite(fav)}
                        className="flex items-center justify-center gap-1.5 py-2.5 bg-[#12141c] border border-gray-900 hover:border-red-900/40 text-xs font-semibold rounded-lg text-gray-300 hover:text-red-400 transition-all active:scale-[0.98]"
                      >
                        <Trash2 size={14} /> {lang === 'ar' ? 'حذف' : 'Supprimer'}
                      </button>
                      <button
                        onClick={() => handleOpenPaymentWorkflow(fav.nom)}
                        className="flex items-center justify-center gap-1.5 py-2.5 bg-[#12141c] border border-gray-900 hover:border-emerald-900/40 text-xs font-semibold rounded-lg text-gray-300 hover:text-emerald-400 transition-all active:scale-[0.98]"
                      >
                        <CreditCard size={14} /> {lang === 'ar' ? 'حجز' : 'Réserver'}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="grid grid-cols-2 gap-2 pt-3 mt-3 border-t border-gray-900 shrink-0">
              <button onClick={exportToCSV} disabled={favorites.length === 0} className="py-3 bg-emerald-600 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-2">
                <AppIcon name="download" size={14} alt="" /> CSV
              </button>
              <button onClick={exportToJSON} disabled={favorites.length === 0} className="py-3 bg-blue-600 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-2">
                <AppIcon name="download" size={14} alt="" /> JSON
              </button>
            </div>
          </div>
        </div>
      )}

      <HistoryPanel
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        token={token}
        lang={lang}
        t={t}
        onRelaunch={handleRelaunchFromHistory}
      />

      {/* MODALE CONFIRMATION SUPPRESSION FAVORI */}
      {favoriteToDelete && (
        <div
          className="fixed inset-0 bg-black/80 backdrop-blur-md z-[60] flex items-center justify-center p-4 animate-fade-in"
          dir={lang === 'ar' ? 'rtl' : 'ltr'}
          onClick={() => setFavoriteToDelete(null)}
        >
          <div
            className="bg-[#12141c] border border-gray-900 rounded-3xl p-6 max-w-sm w-full text-white shadow-2xl space-y-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex flex-col items-center text-center gap-3">
              <div className="w-14 h-14 rounded-2xl bg-red-950/40 border border-red-900/40 flex items-center justify-center">
                <Trash2 size={24} className="text-red-400" />
              </div>
              <h3 className="text-base font-bold text-white">
                {lang === 'ar' ? 'تأكيد الحذف' : 'Confirmer la suppression'}
              </h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                {lang === 'ar' ? (
                  <>هل تريد حذف <span className="text-white font-bold">{favoriteToDelete.nom}</span> من المفضلة؟ لا يمكن التراجع عن هذا الإجراء.</>
                ) : (
                  <>Voulez-vous retirer <span className="text-white font-bold">{favoriteToDelete.nom}</span> de vos favoris ? Cette action est définitive.</>
                )}
              </p>
            </div>

            <div className="flex gap-3 pt-1">
              <button
                type="button"
                onClick={() => setFavoriteToDelete(null)}
                className="flex-1 py-2.5 bg-[#1f2833] hover:bg-gray-800 border border-gray-800 text-gray-300 font-bold rounded-xl text-xs transition-all active:scale-95"
              >
                {lang === 'ar' ? 'إلغاء' : 'Annuler'}
              </button>
              <button
                type="button"
                onClick={confirmRemoveFavorite}
                className="flex-1 py-2.5 bg-red-600 hover:bg-red-500 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-2 transition-all active:scale-95 shadow-lg shadow-red-950/30"
              >
                <Trash2 size={13} />
                {lang === 'ar' ? 'حذف' : 'Supprimer'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ⚡ MODALE INTERNE TARIFS */}
      {paymentModalOpen && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-md z-50 flex items-center justify-center p-6 sm:p-8 animate-fade-in" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
          <div className="bg-[#12141c] border border-purple-950 rounded-3xl p-7 sm:p-8 max-w-5xl w-full text-white shadow-2xl space-y-6 relative overflow-hidden">
            
            <div className="flex justify-between items-start gap-4 border-b border-gray-900 pb-4">
              <h3 className="text-base sm:text-lg font-bold text-purple-400 leading-snug">
                {lang === 'ar' ? 'خيارات حجز الاسم :' : 'Options de réservation pour :'}{' '}
                <span className="text-white font-mono bg-purple-950/40 px-3 py-1 rounded-lg border border-purple-900/40 inline-block mt-1 sm:mt-0">{selectedNameForBooking}</span>
              </h3>
              <button onClick={() => setPaymentModalOpen(false)} className="text-gray-500 hover:text-white font-bold text-lg bg-[#1f2833]/40 w-8 h-8 rounded-full flex items-center justify-center">×</button>
            </div>

            {/* ÉTAPE 1 : LES 3 PLANS */}
            {paymentStep === 1 && (
              <div className="space-y-4">
                {paymentMessage && (
                  <div className={`text-center py-2.5 rounded-xl font-bold border animate-pulse flex items-center justify-center gap-2 ${
                    paymentMessageType === 'success'
                      ? 'text-emerald-400 bg-emerald-950/40 border-emerald-900/20'
                      : 'text-red-400 bg-red-950/40 border-red-900/20'
                  }`}>
                    {paymentMessageType === 'success' && <AppIcon name="party" size={18} alt="" />}
                    {paymentMessageType === 'error' && <AppIcon name="warning" size={18} alt="" />}
                    {paymentMessage}
                  </div>
                )}
                
                <div className="grid md:grid-cols-3 gap-5">
                  
                  {/* FORFAIT 1 : GRATUIT */}
                  <div className="bg-[#1f2833]/10 border border-gray-800 rounded-2xl p-5 flex flex-col justify-between min-h-[280px] hover:border-gray-700 transition-all">
                    <div className="space-y-2">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="text-sm font-bold text-gray-300">Basic Free</h4>
                          <p className="text-[10px] text-gray-500">{lang === 'ar' ? 'حجز مؤقت' : 'Essai & sauvegarde'}</p>
                        </div>
                        <span className="bg-gray-800 text-gray-400 text-[9px] font-bold px-2 py-0.5 rounded">
                          {lang === 'ar' ? 'مجاني' : 'Gratuit'}
                        </span>
                      </div>
                      <div className="text-xl font-black text-white py-1">0 $</div>
                      <ul className="text-[10px] text-gray-400 space-y-1.5 border-t border-gray-950 pt-2">
                        <PlanFeature>{lang === 'ar' ? 'حفظ في المفضلة المحلية' : 'Sauvegarde locale'}</PlanFeature>
                        <PlanFeature>{lang === 'ar' ? 'نسخ سريع للاسم' : 'Copie rapide presse-papier'}</PlanFeature>
                        <PlanFeature icon="cross" className="text-gray-600">{lang === 'ar' ? 'بدون شهادة رقمية' : 'Pas de certificat officiel'}</PlanFeature>
                      </ul>
                    </div>
                    <button
                      onClick={() => handleSelectPlan('free')}
                      disabled={isPaying}
                      className="mt-4 w-full py-2 bg-gray-800 hover:bg-gray-700 font-bold rounded-xl text-[11px] text-white transition-all"
                    >
                      {lang === 'ar' ? 'حجز مجاني' : 'Choisir le Gratuit'}
                    </button>
                  </div>

                  {/* FORFAIT 2 : PRO */}
                  <div className="bg-[#1f2833]/20 border border-purple-900/30 rounded-2xl p-5 flex flex-col justify-between min-h-[280px] hover:border-purple-500/50 transition-all">
                    <div className="space-y-2">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="text-sm font-bold text-white">Pro Plan</h4>
                          <p className="text-[10px] text-gray-500">{lang === 'ar' ? 'للمشاريع الناشئة' : 'Pour les startups'}</p>
                        </div>
                        <span className="bg-purple-950/60 text-purple-400 text-[9px] font-bold px-2 py-0.5 rounded border border-purple-900/30">
                          {lang === 'ar' ? 'أساسي' : 'STANDARD'}
                        </span>
                      </div>
                      <div className="text-xl font-black text-white py-1">19 $ <span className="text-[10px] text-gray-500 font-normal">{lang === 'ar' ? '/ اسم' : '/ nom'}</span></div>
                      <ul className="text-[10px] text-gray-400 space-y-1.5 border-t border-gray-950 pt-2">
                        <PlanFeature>{lang === 'ar' ? 'شهادة حجز رقمية' : 'Certificat de réservation'}</PlanFeature>
                        <PlanFeature>{lang === 'ar' ? 'تصدير كامل CSV/JSON' : 'Export complet CSV/JSON'}</PlanFeature>
                        <PlanFeature>{lang === 'ar' ? 'حماية ضد التكرار 12 شهرًا' : 'Protection anti-doublons 12m'}</PlanFeature>
                      </ul>
                    </div>
                    <button
                      onClick={() => handleSelectPlan('pro')}
                      className="mt-4 w-full py-2 bg-purple-600 hover:bg-purple-700 font-bold rounded-xl text-[11px] text-white transition-all shadow-md"
                    >
                      {lang === 'ar' ? 'شراء Pro' : 'Obtenir le plan Pro'}
                    </button>
                  </div>

                  {/* FORFAIT 3 : MAX */}
                  <div className="bg-purple-950/10 border-2 border-purple-500/40 rounded-2xl p-5 flex flex-col justify-between min-h-[280px] hover:border-purple-500 transition-all relative">
                    <div className={`absolute -top-2.5 ${lang === 'ar' ? 'left-3' : 'right-3'} bg-emerald-600 text-white text-[8px] font-extrabold uppercase px-2 py-0.5 rounded-full shadow-md`}>
                      {lang === 'ar' ? 'موصى به' : 'RECOMMANDÉ'}
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="text-sm font-bold text-purple-400">Max Enterprise</h4>
                          <p className="text-[10px] text-gray-500">{lang === 'ar' ? 'هوية متكاملة' : 'Identité globale premium'}</p>
                        </div>
                      </div>
                      <div className="text-xl font-black text-emerald-400 py-1">49 $ <span className="text-[10px] text-gray-500 font-normal">{lang === 'ar' ? '/ دفعة واحدة' : '/ une fois'}</span></div>
                      <ul className="text-[10px] text-gray-300 space-y-1.5 border-t border-gray-950 pt-2">
                        <PlanFeature icon="star" className="text-purple-300">{lang === 'ar' ? 'كل مميزات خطة Pro' : 'Tout le contenu du plan Pro'}</PlanFeature>
                        <PlanFeature>{lang === 'ar' ? 'شامل نطاق com. متاح' : 'Domaine .com disponible inclus'}</PlanFeature>
                        <PlanFeature>{lang === 'ar' ? 'فحص قانوني للعلامة التجارية' : 'Vérification légale de marque'}</PlanFeature>
                      </ul>
                    </div>
                    <button
                      onClick={() => handleSelectPlan('max')}
                      className="mt-4 w-full py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 font-bold rounded-xl text-[11px] text-white transition-all shadow-lg"
                    >
                      {lang === 'ar' ? 'شراء Max' : 'Obtenir le forfait Max'}
                    </button>
                  </div>

                </div>
              </div>
            )}

            {/* ÉTAPE 2 : FORMULAIRE CB */}
            {paymentStep === 2 && (
              <form onSubmit={handleProcessPaymentSubmit} className="space-y-4 max-w-lg mx-auto text-xs">
                <div className="bg-purple-950/20 border border-purple-900/30 p-3 rounded-xl flex justify-between items-center text-purple-300">
                  <span>{lang === 'ar' ? `نموذج الدفع: خطة ${selectedPlan.toUpperCase()}` : `Formulaire de Paiement : Forfait ${selectedPlan.toUpperCase()}`}</span>
                  <button type="button" onClick={() => setPaymentStep(1)} className="text-[10px] underline hover:text-white">
                    {lang === 'ar' ? '← العودة للخطط' : '← Retour aux plans'}
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-gray-400">{lang === 'ar' ? 'الاسم الشخصي :' : 'Prénom :'}</label>
                    <input type="text" required value={billingData.prenom} onChange={(e) => setBillingData({...billingData, prenom: e.target.value})} className="bg-[#1f2833]/40 border border-gray-800 rounded-xl p-2.5 text-white" />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-gray-400">{lang === 'ar' ? 'الاسم العائلي :' : 'Nom :'}</label>
                    <input type="text" required value={billingData.nom} onChange={(e) => setBillingData({...billingData, nom: e.target.value})} className="bg-[#1f2833]/40 border border-gray-800 rounded-xl p-2.5 text-white" />
                  </div>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-gray-400">{lang === 'ar' ? 'البريد الإلكتروني :' : 'Adresse e-mail :'}</label>
                  <input type="email" required value={billingData.email} onChange={(e) => setBillingData({...billingData, email: e.target.value})} className="bg-[#1f2833]/40 border border-gray-800 rounded-xl p-2.5 text-white" />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-gray-400">{lang === 'ar' ? 'رقم البطاقة البنكية :' : 'Numéro de carte bancaire :'}</label>
                  <input
                    type="text"
                    required
                    inputMode="numeric"
                    placeholder="4242 4242 4242 4242"
                    value={billingData.carte}
                    onChange={(e) => setBillingData({ ...billingData, carte: formatCardNumber(e.target.value) })}
                    className="w-full bg-[#1f2833]/40 border border-gray-800 rounded-xl p-2.5 text-white tracking-widest"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-gray-400">{lang === 'ar' ? 'تاريخ الانتهاء :' : 'Date d\'expiration :'}</label>
                    <input
                      type="text"
                      required
                      inputMode="numeric"
                      placeholder="MM/AA"
                      maxLength={5}
                      value={billingData.expiry}
                      onChange={(e) => setBillingData({ ...billingData, expiry: formatExpiry(e.target.value) })}
                      className="bg-[#1f2833]/40 border border-gray-800 rounded-xl p-2.5 text-white"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-gray-400">CVC</label>
                    <input
                      type="password"
                      required
                      inputMode="numeric"
                      placeholder="123"
                      maxLength={4}
                      value={billingData.cvc}
                      onChange={(e) => setBillingData({ ...billingData, cvc: e.target.value.replace(/\D/g, '').slice(0, 4) })}
                      className="bg-[#1f2833]/40 border border-gray-800 rounded-xl p-2.5 text-white"
                    />
                  </div>
                </div>

                {paymentMessage && (
                  <div className={`text-center py-2 rounded-xl font-bold text-xs flex items-center justify-center gap-2 ${
                    paymentMessageType === 'success'
                      ? 'text-emerald-400 bg-emerald-950/40 border border-emerald-900/30'
                      : 'text-red-400 bg-red-950/40 border border-red-900/30'
                  }`}>
                    {paymentMessageType === 'success' && <AppIcon name="party" size={16} alt="" />}
                    {paymentMessageType === 'error' && <AppIcon name="warning" size={16} alt="" />}
                    {paymentMessage}
                  </div>
                )}

                <div className="flex gap-3 pt-2">
                  <button type="button" onClick={() => setPaymentModalOpen(false)} className="flex-1 py-2.5 bg-gray-900 text-gray-400 font-bold rounded-xl">
                    {lang === 'ar' ? 'إلغاء' : 'Annuler'}
                  </button>
                  <button type="submit" disabled={isPaying} className="flex-1 py-2.5 bg-emerald-600 text-white font-bold rounded-xl flex items-center justify-center gap-2">
                    <CheckCircle size={13} /> {isPaying ? '...' : (lang === 'ar' ? 'تأكيد الدفع' : 'Valider le paiement')}
                  </button>
                </div>
              </form>
            )}

          </div>
        </div>
      )}

      {/* ⚡ MODALE PROPOSITION SUGGESTION NAVBAR - AVEC AJOUT TYPE ET SECTEUR */}
      {navbarSuggestionOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
          <div className="bg-[#12141c] border border-purple-900/30 rounded-3xl p-6 max-w-md w-full text-white space-y-4">
            <div className="flex justify-between items-center border-b border-gray-900 pb-2">
              <h3 className="text-sm font-bold text-purple-400 flex items-center gap-2">
                <AppIcon name="lightbulb" size={18} alt="" />
                {lang === 'ar' ? 'اقتراح اسم جديد' : 'Proposer un nouveau nom'}
              </h3>
              <button onClick={() => setNavbarSuggestionOpen(false)} className="text-gray-500 font-bold hover:text-white">×</button>
            </div>
            
            <form onSubmit={handleFormSuggestionSubmit} className="space-y-4 text-xs">
              {/* Champ Saisie du Nom */}
              <div className="flex flex-col gap-1.5">
                <label className="text-gray-400">{lang === 'ar' ? 'الاسم المقترح :' : 'Nom proposé :'}</label>
                <input 
                  type="text" 
                  required 
                  value={formData.nom} 
                  onChange={(e) => setFormData({...formData, nom: e.target.value})} 
                  placeholder={lang === 'ar' ? 'اكتب الاسم هنا...' : 'Nom proposé...'} 
                  className="w-full bg-[#1f2833]/40 border border-gray-800 rounded-xl p-2.5 text-white focus:border-purple-500 outline-none" 
                />
              </div>

              {/* Sélection Type : Marque / Entreprise */}
              <div className="flex flex-col gap-1.5">
                <label className="text-gray-400">{lang === 'ar' ? 'نوع الاسم :' : 'Type de nom :'}</label>
                <select 
                  value={formData.type} 
                  onChange={(e) => setFormData({...formData, type: e.target.value})} 
                  className="w-full bg-[#1f2833] border border-gray-800 rounded-xl p-2.5 text-white focus:border-purple-500 outline-none"
                >
                  <option value="marque">{lang === 'ar' ? 'علامة تجارية (Marque)' : 'Marque'}</option>
                  <option value="entreprise">{lang === 'ar' ? 'شركة (Entreprise)' : 'Entreprise'}</option>
                </select>
              </div>

              {/* Sélection Secteur d'activité */}
              <div className="flex flex-col gap-1.5">
                <label className="text-gray-400">{lang === 'ar' ? 'قطاع العمل :' : 'Secteur d\'activité :'}</label>
                <select 
                  value={formData.secteur} 
                  onChange={(e) => setFormData({...formData, secteur: e.target.value})} 
                  className="w-full bg-[#1f2833] border border-gray-800 rounded-xl p-2.5 text-white focus:border-purple-500 outline-none"
                >
                  <option value="Tech">{lang === 'ar' ? 'تكنولوجيا (Tech)' : 'Tech'}</option>
                  <option value="Food">{lang === 'ar' ? 'أغذية ومطاعم (Food)' : 'Food'}</option>
                  <option value="General">{lang === 'ar' ? 'عام (Général)' : 'Général'}</option>
                  <option value="Luxe">{lang === 'ar' ? 'فاخر / رفاهية (Luxe)' : 'Luxe'}</option>
                </select>
              </div>

              {/* Zone Messages d'envoi */}
              {submitMessage && (
                <div className={`text-center py-2 rounded-xl border animate-fade-in text-xs flex items-center justify-center gap-2 ${
                  submitMessage.includes('succès') || submitMessage.includes('Envoyé') || submitMessage.includes('تم إرسال')
                    ? 'text-purple-300 bg-purple-950/40 border-purple-900/30'
                    : 'text-red-400 bg-red-950/40 border-red-900/30'
                }`}>
                  {(submitMessage.includes('succès') || submitMessage.includes('Envoyé') || submitMessage.includes('تم إرسال'))
                    ? <AppIcon name="party" size={16} alt="" />
                    : <AppIcon name="warning" size={16} alt="" />}
                  {submitMessage}
                </div>
              )}

              {/* Actions de validation */}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setNavbarSuggestionOpen(false)} className="flex-1 py-2.5 bg-gray-900 text-gray-400 font-bold rounded-xl hover:bg-gray-800 transition-all">
                  {lang === 'ar' ? 'إلغاء' : 'Annuler'}
                </button>
                <button type="submit" disabled={isSubmitting} className="flex-1 py-2.5 bg-purple-600 text-white font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-purple-700 transition-all">
                  <Send size={12} /> {isSubmitting ? '...' : (lang === 'ar' ? 'إرسال الاقتراح' : 'Envoyer')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
