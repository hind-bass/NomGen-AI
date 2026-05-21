import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Globe, Heart, User } from 'lucide-react'; // Installez lucide-react si nécessaire via npm

export default function Navbar({ onOpenFavorites }) {
  const { lang, setLang, favorites } = useApp();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  return (
    <nav className="w-full h-16 px-8 flex justify-between items-center bg-[#0b0c10] border-b border-gray-900">
      <div className="flex items-center gap-2 font-bold text-white text-xl tracking-wide">
        <span className="p-2 bg-purple-600 rounded-xl text-sm">✨</span> BrandForge
      </div>

      <div className="flex items-center gap-4 relative">
        {/* BOUTON LANGUE DROPDOWN */}
        <div className="relative">
          <button 
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 bg-[#1f2833] text-white px-4 py-2 rounded-full border border-gray-800 hover:border-purple-500 transition-all text-sm font-medium"
          >
            <Globe size={16} />
            {lang === 'fr' ? 'FR' : 'AR'}
          </button>
          
          {dropdownOpen && (
            <div className={`absolute mt-2 w-32 bg-[#1f2833] border border-gray-800 rounded-xl shadow-xl z-50 ${lang === 'ar' ? 'left-0' : 'right-0'}`}>
              <button 
                onClick={() => { setLang('fr'); setDropdownOpen(false); }}
                className="w-full text-left px-4 py-2 text-white hover:bg-purple-600 rounded-t-xl text-sm"
              >
                Français
              </button>
              <button 
                onClick={() => { setLang('ar'); setDropdownOpen(false); }}
                className="w-full text-left px-4 py-3 text-white hover:bg-purple-600 rounded-b-xl text-sm font-arabic"
              >
                العربية
              </button>
            </div>
          )}
        </div>

        {/* BOUTON FAVORIS AVEC COMPTEUR DE BADGE */}
        <button 
          onClick={onOpenFavorites}
          className="relative p-2.5 bg-[#1f2833] text-white rounded-full border border-gray-800 hover:border-purple-500 transition-all"
        >
          <Heart size={18} className={favorites.length > 0 ? "fill-purple-500 text-purple-500" : ""} />
          {favorites.length > 0 && (
            <span className="absolute -top-1 -right-1 bg-purple-600 text-white text-[10px] w-5 h-5 rounded-full flex items-center justify-center font-bold">
              {favorites.length}
            </span>
          )}
        </button>

      </div>
    </nav>
  );
}