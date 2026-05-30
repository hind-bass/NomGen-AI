import React, { useState } from 'react';
import Navbar from './components/Navbar';
import MainSelection from './components/MainSelection';
import PromptScreen from './components/PromptScreen';
import CardsScreen from './components/CardsScreen';
import AuthScreen from './components/AuthScreen';
import { useApp } from './context/AppContext'; // Importation du contexte global

export default function App() {
  const [screen, setScreen] = useState('home'); // 'home', 'prompt', 'cards'
  const [generationType, setGenerationType] = useState(null);
  const [favoritesOpen, setFavoritesOpen] = useState(false);
  const [config, setConfig] = useState({ prompt: '', style: 'Tous' });

  // Extraction des variables et fonctions depuis le Context global
  const { lang, t, user, loginUser, favorites, exportToCSV, exportToJSON } = useApp();

  const handleSelectMode = (type) => {
    setGenerationType(type);
    setScreen('prompt');
  };

  const handleGenerate = (data) => {
    setConfig(data);
    setScreen('cards'); 
  };

  // ⚡ SÉCURITÉ : Si l'utilisateur n'est pas connecté, on bloque sur l'authentification
  if (!user) {
    return <AuthScreen onAuthSuccess={loginUser} />;
  }

  return (
    <div className="min-h-screen bg-[#0b0c10] font-sans antialiased flex flex-col">
      
      {/* LA NAVBAR BARRE DE NAVIGATION UNIFIÉE (Toujours visible après connexion) */}
      <Navbar onOpenFavorites={() => setFavoritesOpen(true)} />

      {/* ZONE DE CONTENU DYNAMIQUE SELON L'ÉCRAN ACUTEL */}
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
              <div className="space-y-3 max-h-[calc(100vh-14rem)] overflow-y-auto pr-1 custom-scrollbar">
                {favorites.length === 0 ? (
                  <div className="text-center py-12 text-gray-600 text-sm">
                    <p className="text-2xl mb-2">📁</p>
                    <p>{t('noFav')}</p>
                  </div>
                ) : (
                  favorites.map((fav, i) => (
                    <div 
                      key={i} 
                      className="flex justify-between items-center p-4 bg-[#1f2833]/40 hover:bg-[#1f2833]/80 border border-gray-900 rounded-xl transition-all group"
                    >
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
                  ))
                )}
              </div>
            </div>

            {/* BAS : Les 2 boutons d'exportation (CSV et JSON) */}
            <div className="grid grid-cols-2 gap-3 pt-4 border-t border-gray-900">
              {/* BOUTON EXPORT CSV */}
              <button
                onClick={exportToCSV}
                disabled={favorites.length === 0}
                className="py-3 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-20 disabled:hover:bg-emerald-600 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-2 transition-all shadow-lg shadow-emerald-950/20 active:scale-95"
              >
                📥 {lang === 'ar' ? 'تصدير CSV' : 'Exporter CSV'}
              </button>

              {/* BOUTON EXPORT JSON */}
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

    </div>
  );
}
