import React, { useState } from 'react';
import Navbar from './components/Navbar';
import MainSelection from './components/MainSelection';
import PromptScreen from './components/PromptScreen';
import CardsScreen from './components/CardsScreen';
import AuthScreen from './components/AuthScreen';
import AdminDashboard from './components/AdminDashboard'; // Importation du futur écran Admin
import { useApp } from './context/AppContext'; // Importation du contexte global
import { Share2, CreditCard } from 'lucide-react'; // Icônes pour les nouvelles actions

export default function App() {
  const [screen, setScreen] = useState('home'); // 'home', 'prompt', 'cards', 'admin'
  const [generationType, setGenerationType] = useState(null);
  const [favoritesOpen, setFavoritesOpen] = useState(false);
  const [config, setConfig] = useState({ prompt: '', style: 'Tous' });

  // États pour la modale de suggestion communautaire
  const [suggestionModalOpen, setSuggestionModalOpen] = useState(false);
  const [selectedFavToSuggest, setSelectedFavToSuggest] = useState(null);
  const [isSubmittingSuggestion, setIsSubmittingSuggestion] = useState(false);
  const [suggestionMessage, setSuggestionMessage] = useState('');

  // Extraction des variables et fonctions depuis le Context global (avec jeton et userRole)
  const { lang, t, token, user, userRole, loginUser, favorites, exportToCSV, exportToJSON } = useApp();

  const handleSelectMode = (type) => {
    setGenerationType(type);
    setScreen('prompt');
  };

  const handleGenerate = (data) => {
    setConfig(data);
    setScreen('cards'); 
  };

  // Actionneur du bouton Premium Stripe Link
  const handleReserveName = (name) => {
    // Remplacer par votre lien Stripe de test réel généré sur votre Dashboard Stripe
    const stripePaymentLink = `https://buy.stripe.com/test_6oE5mS8df9v0bM49AA?client_reference_id=${user?.id}&prefilled_email=${encodeURIComponent(user?.email)}&item_name=${encodeURIComponent(name)}`;
    window.open(stripePaymentLink, "_blank");
  };

  // Envoi du formulaire de suggestion communautaire au backend
  const handlePostSuggestion = async (e) => {
    e.preventDefault();
    if (!selectedFavToSuggest) return;

    try {
      setIsSubmittingSuggestion(true);
      setSuggestionMessage('');

      const response = await fetch('http://127.0.0.1:8000/api/suggestions', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` // Transmission du jeton JWT pour authentification
        },
        body: JSON.stringify({
          nom: selectedFavToSuggest.nom,
          categorie: selectedFavToSuggest.style || selectedFavToSuggest.secteur || "Tous",
          langue: lang
        })
      });

      if (response.ok) {
        setSuggestionMessage(lang === 'ar' ? 'تم ارسال اقتراحك بنجاح للمراجعة !' : 'Suggestion envoyée avec succès pour modération !');
        setTimeout(() => {
          setSuggestionModalOpen(false);
          setSuggestionMessage('');
        }, 2000);
      } else {
        setSuggestionMessage('Erreur lors du traitement de la suggestion.');
      }
    } catch (error) {
      console.error("Erreur d'envoi:", error);
      setSuggestionMessage('Impossible de joindre le serveur.');
    } finally {
      setIsSubmittingSuggestion(false);
    }
  };

  // ⚡ SÉCURITÉ : Si l'utilisateur n'est pas connecté, on bloque sur l'authentification
  if (!user) {
    return <AuthScreen onAuthSuccess={loginUser} />;
  }

  return (
    <div className="min-h-screen bg-[#0b0c10] font-sans antialiased flex flex-col">
      
      {/* LA NAVBAR BARRE DE NAVIGATION UNIFIÉE (Toujours visible après connexion) */}
      <Navbar onOpenFavorites={() => setFavoritesOpen(true)} />

      {/* Raccourci vers le Dashboard Administrateur visible uniquement pour le rôle 'admin' */}
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

      {/* ZONE DE CONTENU DYNAMIQUE SELON L'ÉCRAN ACTUEL */}
      <main className="flex-1">
        {screen === 'home' && (
          <MainSelection onSelectMode={handleSelectMode} />
        )}

        {screen === 'prompt' && (
          <div className="animate-fade-in">
            <PromptScreen 
              generationType={generationType}
              onGoBack={() => setScreen('home')}
              onGenerate={handleGenerate}
            />
          </div>
        )}

        {screen === 'cards' && (
          <CardsScreen 
            config={config}
            generationType={generationType}
            onGoBack={() => setScreen('prompt')}
          />
        )}

        {/* ⚡ NOUVEAUTÉ : Écran d'administration des suggestions */}
        {screen === 'admin' && userRole === 'admin' && (
          <AdminDashboard onGoBack={() => setScreen('home')} />
        )}
      </main>

      {/* MODAL / TIROIR COULISSANT DES FAVORIS */}
      {favoritesOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-end animate-fade-in">
          {/* Fond cliquable pour fermer */}
          <div className="flex-1" onClick={() => setFavoritesOpen(false)} />
          
          {/* Conteneur du tiroir */}
          <div className={`w-full max-w-md bg-[#12141c] h-full p-6 text-white border-l border-gray-900 shadow-2xl flex flex-col justify-between transform transition-transform duration-300 ${
            lang === 'ar' ? 'border-r border-l-0' : 'border-l'
          }`}>
            
            {/* HAUT : Titre et bouton Fermer */}
            <div>
              <div className="flex justify-between items-center border-b border-gray-900 pb-4 mb-6">
                <h2 className="text-xl font-bold tracking-wide flex items-center gap-2">
                  <span className="text-purple-500">❤️</span> {t('favTitle')}
                </h2>
                <button 
                  onClick={() => setFavoritesOpen(false)} 
                  className="text-xs bg-[#1f2833] hover:bg-purple-600 px-3 py-1.5 rounded-full text-gray-300 hover:text-white transition-all"
                >
                  {lang === 'ar' ? 'إغلاق ×' : 'Fermer ×'}
                </button>
              </div>

              {/* MILIEU : Liste des favoris défilante */}
              <div className="space-y-3 max-h-[calc(100vh-16rem)] overflow-y-auto pr-1 custom-scrollbar">
                {favorites.length === 0 ? (
                  <div className="text-center py-12 text-gray-600 text-sm">
                    <p className="text-2xl mb-2">📁</p>
                    <p>{t('noFav')}</p>
                  </div>
                ) : (
                  favorites.map((fav, i) => (
                    <div 
                      key={i} 
                      className="flex flex-col gap-3 p-4 bg-[#1f2833]/40 hover:bg-[#1f2833]/60 border border-gray-900 rounded-xl transition-all group"
                    >
                      <div className="flex justify-between items-center">
                        <div className={`flex flex-col gap-1 ${lang === 'ar' ? 'text-right' : 'text-left'}`}>
                          <h4 className="text-white font-bold tracking-wide text-base">{fav.nom}</h4>
                          <div className="flex items-center gap-1.5">
                            <span className="text-[10px] uppercase font-bold text-purple-400 bg-purple-950/40 px-2 py-0.5 rounded-md border border-purple-900/30">
                              {t((fav.style || fav.secteur || "tech").toLowerCase().trim())}
                            </span>
                          </div>
                        </div>
                        {fav.score && (
                          <span className="text-xs font-bold text-emerald-400 bg-emerald-950/30 px-2.5 py-1 rounded-full border border-emerald-900/30">
                            {fav.score}/100
                          </span>
                        )}
                      </div>

                      {/* ⚡ LE COUTEAU SUISSE : Actions rapides par favori (Suggérer & Réserver Stripe) */}
                      <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-900/60 opacity-90 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => {
                            setSelectedFavToSuggest(fav);
                            setSuggestionModalOpen(true);
                          }}
                          className="flex items-center justify-center gap-1.5 py-1.5 bg-[#12141c] hover:bg-purple-900/30 border border-gray-800 text-[11px] font-medium rounded-lg text-gray-300 hover:text-purple-400 transition-all"
                        >
                          <Share2 size={12} />
                          <span>{lang === 'ar' ? 'اقتراح الاسم' : 'Proposer'}</span>
                        </button>
                        
                        <button
                          onClick={() => handleReserveName(fav.nom)}
                          className="flex items-center justify-center gap-1.5 py-1.5 bg-[#12141c] hover:bg-emerald-950/40 border border-gray-800 text-[11px] font-medium rounded-lg text-gray-300 hover:text-emerald-400 transition-all"
                        >
                          <CreditCard size={12} />
                          <span>{lang === 'ar' ? 'حجز (Premium)' : 'Réserver'}</span>
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* BAS : Les 2 boutons d'exportation (CSV et JSON) */}
            <div className="grid grid-cols-2 gap-3 pt-4 border-t border-gray-900">
              <button
                onClick={exportToCSV}
                disabled={favorites.length === 0}
                className="py-3 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-20 disabled:hover:bg-emerald-600 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-2 transition-all shadow-lg shadow-emerald-950/20 active:scale-95"
              >
                📥 {lang === 'ar' ? 'تصدير CSV' : 'Exporter CSV'}
              </button>

              <button
                onClick={exportToJSON}
                disabled={favorites.length === 0}
                className="py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-20 disabled:hover:bg-blue-600 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-2 transition-all shadow-lg shadow-blue-950/20 active:scale-95"
              >
                📥 {lang === 'ar' ? 'تصدير JSON' : 'Exporter JSON'}
              </button>
            </div>

          </div>
        </div>
      )}

      {/* ⚡ NOUVEAUTÉ : MODALE FORMULAIRE DE SUGGESTION COMMUNAUTAIRE */}
      {suggestionModalOpen && selectedFavToSuggest && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-[#12141c] border border-gray-900 rounded-3xl p-6 max-w-sm w-full text-white shadow-2xl space-y-4">
            <h3 className="text-lg font-bold tracking-wide text-purple-400">
              {lang === 'ar' ? '🤝 اقتراح الاسم للمجتمع' : '🤝 Partager ce nom'}
            </h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              {lang === 'ar' 
                ? `هل تريد فعلاً اقتراح الاسم "${selectedFavToSuggest.nom}" لمراجعته وإضافته لقاعدة البيانات العامة؟` 
                : `Souhaitez-vous soumettre le nom "${selectedFavToSuggest.nom}" à la communauté ? Après validation d'un administrateur, il rejoindra le dataset.`}
            </p>

            {suggestionMessage && (
              <div className="text-xs text-center font-semibold text-purple-300 py-1 bg-purple-950/30 rounded-lg">
                {suggestionMessage}
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => setSuggestionModalOpen(false)}
                className="flex-1 py-2.5 bg-gray-900 hover:bg-gray-800 text-xs font-bold rounded-xl text-gray-400 transition-all"
              >
                {lang === 'ar' ? 'إلغاء' : 'Annuler'}
              </button>
              <button
                onClick={handlePostSuggestion}
                disabled={isSubmittingSuggestion}
                className="flex-1 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-xs font-bold rounded-xl text-white transition-all shadow-lg shadow-purple-950/30"
              >
                {isSubmittingSuggestion ? '...' : (lang === 'ar' ? 'تأكيد الاقتراح' : 'Confirmer')}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
