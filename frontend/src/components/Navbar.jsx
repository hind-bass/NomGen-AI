import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Globe, Heart, User, LogOut, PlusCircle, Clock } from 'lucide-react';
import logoImage from '../assets/image.png';

export default function Navbar({ onOpenFavorites, onOpenHistory, onOpenSuggestion }) {
  const { lang, setLang, favorites, user, logoutUser } = useApp();
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);

  // Gestionnaire de déconnexion sécurisé pour fermer le menu localement avant de purger le token
  const handleNavbarLogout = () => {
    setProfileDropdownOpen(false);
    logoutUser(); // Déclenche le nettoyage global du token et de l'utilisateur
  };

  return (
    <nav className="w-full h-16 px-8 flex justify-between items-center bg-[#0b0c10] border-b border-gray-950 relative z-50">
      
      {/* GAUCHE : LOGO PERSONNALISÉ UNIFIÉ */}
      <div className="flex items-center gap-3 font-bold text-white text-sm tracking-wider select-none">
        <div className="w-12 h-12 rounded-xl overflow-hidden flex items-center justify-center border border-purple-500/20 shadow-md shadow-purple-950/40 bg-black/20">
          <img 
            src={logoImage} 
            alt="BrandForge BF Logo" 
            className="w-full h-full object-cover"
          />
        </div>
        <span>BrandForge</span>
      </div>

      {/* DROITE : BLOC D'ACTIONS */}
      <div className="flex items-center gap-4 relative">
        
        {/* 1. NOUVEAU : BOUTON PROPOSER UN NOM */}
        <button
          onClick={() => {
            onOpenSuggestion();
            setLangDropdownOpen(false);    // Évite la superposition des menus
            setProfileDropdownOpen(false);
          }}
          className="flex items-center gap-1.5 px-3.5 py-1.5 bg-purple-900/20 hover:bg-purple-600 border border-purple-600/30 text-xs font-semibold rounded-full text-purple-300 hover:text-white transition-all active:scale-95"
        >
          <PlusCircle size={13} />
          <span>{lang === 'ar' ? 'إقتراح اسم' : 'Proposer un nom'}</span>
        </button>

        {/* 2. SÉLECTEUR DE LANGUE DROPDOWN STYLISÉ */}
        <div className="relative">
          <button 
            onClick={() => {
              setLangDropdownOpen(!langDropdownOpen);
              setProfileDropdownOpen(false); // Ferme le profil si ouvert
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#12141c] border border-gray-950 text-xs font-semibold rounded-full text-white hover:text-purple-400 hover:border-purple-600/30 transition-all"
          >
            <Globe size={13} />
            <span className="uppercase">{lang}</span>
          </button>
          
          {langDropdownOpen && (
            <div className={`absolute mt-2 w-32 bg-[#12141c] border border-gray-950 rounded-xl shadow-2xl z-50 ${
              lang === 'ar' ? 'left-0' : 'right-0'
            } animate-fade-in`}>
              <button 
                onClick={() => { setLang('fr'); setLangDropdownOpen(false); }}
                className="w-full text-left px-4 py-2 text-white hover:bg-purple-600/20 hover:text-purple-400 rounded-t-xl text-xs font-medium transition-all"
              >
                Français
              </button>
              <button 
                onClick={() => { setLang('ar'); setLangDropdownOpen(false); }}
                className="w-full text-left px-4 py-2.5 text-white hover:bg-purple-600/20 hover:text-purple-400 rounded-b-xl text-xs font-medium transition-all"
              >
                العربية
              </button>
            </div>
          )}
        </div>

        {/* 3. HISTORIQUE DES GÉNÉRATIONS */}
        <button
          onClick={onOpenHistory}
          className="p-2 bg-[#12141c] border border-gray-950 rounded-full text-white hover:text-blue-400 hover:border-blue-500/20 transition-all"
          title={lang === 'ar' ? 'السجل' : 'Historique'}
        >
          <Clock size={15} />
        </button>

        {/* 4. BOUTON FAVORIS AVEC COMPTEUR DE BADGE DISCRET */}
        <button 
          onClick={onOpenFavorites}
          className="relative p-2 bg-[#12141c] border border-gray-950 rounded-full text-white hover:text-emerald-400 hover:border-emerald-500/20 transition-all"
        >
          <Heart size={15} className={favorites.length > 0 ? "fill-emerald-400 text-emerald-400" : ""} />
          {favorites.length > 0 && (
            <span className="absolute -top-1 -right-1 bg-purple-600 text-white text-[9px] w-4 h-4 rounded-full flex items-center justify-center font-bold shadow-md">
              {favorites.length}
            </span>
          )}
        </button>

        {/* 5. BOUTON AVATAR DE PROFIL USER ET TIROIR DÉROULANT */}
        <div className="relative">
          <button 
            onClick={() => {
              setProfileDropdownOpen(!profileDropdownOpen);
              setLangDropdownOpen(false); // Ferme la langue si ouverte
            }}
            className="p-2 bg-[#12141c] border border-purple-600/30 rounded-full text-purple-400 hover:border-purple-600 transition-all flex items-center justify-center"
          >
            <User size={15} />
          </button>

          {profileDropdownOpen && (
            <div className={`absolute mt-2 w-56 bg-[#12141c] border border-gray-950 rounded-2xl p-4 shadow-2xl flex flex-col gap-3 ${
              lang === 'ar' ? 'left-0' : 'right-0'
            } animate-fade-in`}>
              <div className="border-b border-gray-900 pb-2">
                <p className="text-[10px] text-gray-500 font-semibold uppercase tracking-wide">
                  {lang === 'ar' ? 'مسجل كـ' : 'Connecté en tant que'}
                </p>
                <p className="text-xs text-white font-medium truncate mt-0.5">
                  {user?.email || 'user@example.com'}
                </p>
              </div>
              <button 
                onClick={handleNavbarLogout}
                className="w-full py-2 px-3 bg-red-950/20 hover:bg-red-950/50 border border-red-900/30 text-red-400 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all active:scale-95"
              >
                <LogOut size={12} />
                <span>{lang === 'ar' ? 'تسجيل الخروج' : 'Se déconnecter'}</span>
              </button>
            </div>
          )}
        </div>

      </div>
    </nav>
  );
}