import React, { useState } from 'react';
import Navbar from './components/Navbar';
import MainSelection from './components/MainSelection';
import PromptScreen from './components/PromptScreen';
import CardsScreen from './components/CardsScreen';
import AuthScreen from './components/AuthScreen';
import AdminDashboard from './components/AdminDashboard'; 
import { useApp } from './context/AppContext'; 
import { Trash2, CreditCard, Send, CheckCircle } from 'lucide-react'; 

export default function App() {
  const [screen, setScreen] = useState('home'); // 'home', 'prompt', 'cards', 'admin'
  const [generationType, setGenerationType] = useState(null);
  const [favoritesOpen, setFavoritesOpen] = useState(false);
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
  const [billingData, setBillingData] = useState({ nom: '', prenom: '', email: '', carte: '' });
  const [isPaying, setIsPaying] = useState(false);
  const [paymentMessage, setPaymentMessage] = useState('');

  const { lang, t, token, user, userRole, loginUser, favorites, removeFavorite, exportToCSV, exportToJSON } = useApp();

  const handleSelectMode = (type) => {
    setGenerationType(type);
    setScreen('prompt');
  };

  const handleGenerate = (data) => {
    setConfig(data);
    setScreen('cards'); 
  };

  // ⚡ OUVERTURE DU WORKFLOW DE RÉSERVATION
  const handleOpenPaymentWorkflow = (name) => {
    setSelectedNameForBooking(name);
    setBillingData({
      nom: user?.nom?.split(' ')[1] || '',
      prenom: user?.nom?.split(' ')[0] || '',
      email: user?.email || '',
      carte: ''
    });
    setPaymentStep(1); 
    setPaymentMessage('');
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

  // Envoi global de la réservation vers FastAPI
  const handleProcessReservation = async (plan, dataToSend) => {
    try {
      setIsPaying(true);
      setPaymentMessage('');

      const response = await fetch('http://127.0.0.1:8000/api/reservations/pay', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          nom_propose: selectedNameForBooking,
          forfait: plan,
          client_nom: dataToSend.nom,
          client_prenom: dataToSend.prenom,
          client_email: dataToSend.email,
          numero_carte: dataToSend.carte
        })
      });

      if (response.ok) {
        setPaymentMessage(
          lang === 'ar' 
            ? '🎉 تم حجز الاسم بنجاح!' 
            : '🎉 Nom réservé avec succès !'
        );
        setTimeout(() => {
          setPaymentModalOpen(false);
          setPaymentStep(1);
          setPaymentMessage('');
        }, 3000);
      } else {
        setPaymentMessage(lang === 'ar' ? 'حدث خطأ أثناء المعالجة.' : 'Erreur lors du traitement de la réservation.');
      }
    } catch (error) {
      console.error(error);
      setPaymentMessage(lang === 'ar' ? 'خطأ في الاتصال بالخادم.' : 'Impossible de joindre le serveur.');
    } finally {
      setIsPaying(false);
    }
  };

  const handleProcessPaymentSubmit = (e) => {
    e.preventDefault();
    handleProcessReservation(selectedPlan, billingData);
  };

  // ⚡ SOUMISSION SUGGESTION NAVBAR
  const handleFormSuggestionSubmit = async (e) => {
    e.preventDefault();
    if (!formData.nom.trim()) return;

    try {
      setIsSubmitting(true);
      setSubmitMessage('');

      const response = await fetch('http://127.0.0.1:8000/api/suggestions', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({
          nom: formData.nom,
          categorie: formData.type,   
          secteur: formData.secteur,   
          langue: lang
        })
      });

      if (response.ok) {
        setSubmitMessage(lang === 'ar' ? 'تم إرسال اقتراحك بنجاح!' : 'Envoyé avec succès ! En attente de modération.');
        setFormData({ nom: '', type: 'marque', secteur: 'Tech' }); 
        setTimeout(() => {
          setNavbarSuggestionOpen(false);
          setSubmitMessage('');
        }, 2500);
      } else {
        setSubmitMessage(lang === 'ar' ? 'حدث خطأ أثناء الإرسال.' : 'Erreur lors de l\'envoi.');
      }
    } catch (error) {
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!user) {
    return <AuthScreen onAuthSuccess={loginUser} />;
  }

  return (
    <div className="min-h-screen bg-[#0b0c10] font-sans antialiased flex flex-col">
      
      <Navbar 
        onOpenFavorites={() => setFavoritesOpen(true)} 
        onOpenSuggestion={() => setNavbarSuggestionOpen(true)} 
      />

      {userRole === 'admin' && (
        <div className="bg-purple-900/40 border-b border-purple-800 px-6 py-2 flex justify-between items-center text-xs text-purple-200">
          <span>🛡️ Mode Administrateur Activé</span>
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
            <PromptScreen generationType={generationType} onGoBack={() => setScreen('home')} onGenerate={handleGenerate} />
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
          <div className="w-full max-w-md bg-[#12141c] h-full p-6 text-white shadow-2xl flex flex-col justify-between" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
            <div>
              <div className="flex justify-between items-center border-b border-gray-900 pb-4 mb-6">
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <span className="text-purple-500">❤️</span> {t('favTitle')}
                </h2>
                <button onClick={() => setFavoritesOpen(false)} className="text-xs bg-[#1f2833] hover:bg-purple-600 px-3 py-1.5 rounded-full text-gray-300">
                  {lang === 'ar' ? 'إغلاق ×' : 'Fermer ×'}
                </button>
              </div>

              <div className="space-y-3 max-h-[calc(100vh-16rem)] overflow-y-auto">
                {favorites.length === 0 ? (
                  <div className="text-center py-12 text-gray-600 text-sm">📁 {t('noFav')}</div>
                ) : (
                  favorites.map((fav, i) => (
                    <div key={fav.id || i} className="flex flex-col gap-3 p-4 bg-[#1f2833]/40 border border-gray-900 rounded-xl group">
                      <div className="flex justify-between items-center">
                        <h4 className="text-white font-bold">{fav.nom}</h4>
                        {fav.score && <span className="text-xs font-bold text-emerald-400 bg-emerald-950/30 px-2.5 py-1 rounded-full">{fav.score}/100</span>}
                      </div>
                      <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-900/60">
                        <button onClick={() => removeFavorite(fav.id || fav.nom)} className="flex items-center justify-center gap-1.5 py-1.5 bg-[#12141c] text-[11px] rounded-lg text-gray-300 hover:text-red-400">
                          <Trash2 size={12} /> {lang === 'ar' ? 'حذف' : 'Supprimer'}
                        </button>
                        <button onClick={() => handleOpenPaymentWorkflow(fav.nom)} className="flex items-center justify-center gap-1.5 py-1.5 bg-[#12141c] text-[11px] rounded-lg text-gray-300 hover:text-emerald-400">
                          <CreditCard size={12} /> {lang === 'ar' ? 'حجز' : 'Réserver'}
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 pt-4 border-t border-gray-900">
              <button onClick={exportToCSV} disabled={favorites.length === 0} className="py-3 bg-emerald-600 text-white font-bold rounded-xl text-xs">📥 CSV</button>
              <button onClick={exportToJSON} disabled={favorites.length === 0} className="py-3 bg-blue-600 text-white font-bold rounded-xl text-xs">📥 JSON</button>
            </div>
          </div>
        </div>
      )}

      {/* ⚡ MODALE INTERNE TARIFS */}
      {paymentModalOpen && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-md z-50 flex items-center justify-center p-4 animate-fade-in" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
          <div className="bg-[#12141c] border border-purple-950 rounded-3xl p-6 max-w-4xl w-full text-white shadow-2xl space-y-6 relative overflow-hidden">
            
            <div className="flex justify-between items-center border-b border-gray-900 pb-3">
              <h3 className="text-base font-bold text-purple-400">
                {lang === 'ar' ? 'خيارات حجز الاسم :' : 'Options de réservation pour :'} <span className="text-white font-mono bg-purple-950/40 px-3 py-1 rounded-lg border border-purple-900/40">{selectedNameForBooking}</span>
              </h3>
              <button onClick={() => setPaymentModalOpen(false)} className="text-gray-500 hover:text-white font-bold text-lg bg-[#1f2833]/40 w-8 h-8 rounded-full flex items-center justify-center">×</button>
            </div>

            {/* ÉTAPE 1 : LES 3 PLANS */}
            {paymentStep === 1 && (
              <div className="space-y-4">
                {paymentMessage && (
                  <div className="text-center text-emerald-400 bg-emerald-950/40 py-2.5 rounded-xl font-bold border border-emerald-900/20 animate-pulse">
                    {paymentMessage}
                  </div>
                )}
                
                <div className="grid md:grid-cols-3 gap-4">
                  
                  {/* FORFAIT 1 : GRATUIT */}
                  <div className="bg-[#1f2833]/10 border border-gray-800 rounded-2xl p-4 flex flex-col justify-between hover:border-gray-700 transition-all">
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
                        <li>✓ {lang === 'ar' ? 'حفظ في المفضلة المحلية' : 'Sauvegarde locale'}</li>
                        <li>✓ {lang === 'ar' ? 'نسخ سريع للاسم' : 'Copie rapide presse-papier'}</li>
                        <li className="text-gray-600">✗ {lang === 'ar' ? 'بدون شهادة رقمية' : 'Pas de certificat officiel'}</li>
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
                  <div className="bg-[#1f2833]/20 border border-purple-900/30 rounded-2xl p-4 flex flex-col justify-between hover:border-purple-500/50 transition-all">
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
                        <li>✓ {lang === 'ar' ? 'شهادة حجز رقمية' : 'Certificat de réservation'}</li>
                        <li>✓ {lang === 'ar' ? 'تصدير كامل CSV/JSON' : 'Export complet CSV/JSON'}</li>
                        <li>✓ {lang === 'ar' ? 'حماية ضد التكرار 12 شهرًا' : 'Protection anti-doublons 12m'}</li>
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
                  <div className="bg-purple-950/10 border-2 border-purple-500/40 rounded-2xl p-4 flex flex-col justify-between hover:border-purple-500 transition-all relative">
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
                        <li className="text-purple-300">{lang === 'ar' ? '★ كل مميزات خطة Pro' : '★ Tout le contenu du plan Pro'}</li>
                        <li>✓ {lang === 'ar' ? 'شامل نطاق com. متاح' : 'Domaine .com disponible inclus'}</li>
                        <li>✓ {lang === 'ar' ? 'فحص قانوني للعلامة التجارية' : 'Vérification légale de marque'}</li>
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
              <form onSubmit={handleProcessPaymentSubmit} className="space-y-4 max-w-md mx-auto text-xs">
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
                  <input type="text" required placeholder="4242 4242 4242 4242" value={billingData.carte} onChange={(e) => setBillingData({...billingData, carte: e.target.value})} className="w-full bg-[#1f2833]/40 border border-gray-800 rounded-xl p-2.5 text-white tracking-widest" />
                </div>

                {paymentMessage && <div className="text-center text-emerald-400 bg-emerald-950/40 py-2 rounded-xl font-bold">{paymentMessage}</div>}

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
              <h3 className="text-sm font-bold text-purple-400">💡 {lang === 'ar' ? 'اقتراح اسم جديد' : 'Proposer un nouveau nom'}</h3>
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
                <div className="text-purple-300 text-center bg-purple-950/40 py-2 rounded-xl border border-purple-900/30 animate-fade-in">
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
