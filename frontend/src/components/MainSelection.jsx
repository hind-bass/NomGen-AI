import React from 'react';
import { useApp } from '../context/AppContext';
import { Building2, Tag, ArrowRight, ArrowLeft } from 'lucide-react';

export default function MainSelection({ onSelectMode }) {
  const { t, lang } = useApp();

  // Gestion dynamique de la flèche selon la direction de lecture (LTR / RTL)
  const ArrowIcon = lang === 'ar' ? ArrowLeft : ArrowRight;

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] bg-[#0b0c10] px-4">
      
      {/* SECTION DU TITRE */}
      <div className="text-center mb-10 animate-fade-in">
        <h1 className="text-4xl md:text-5xl font-serif font-bold text-white mb-3 tracking-tight">
          {t('title')}
        </h1>
        <p className="text-gray-500 text-sm max-w-md mx-auto leading-relaxed">
          {t('subtitle')}
        </p>
      </div>

      {/* BOUTONS DES CARTES DE SÉLECTION */}
      <div className="w-full max-w-xl flex flex-col gap-4">
        
        {/* OPTION 1 : NOMS D'ENTREPRISE */}
        <button
          onClick={() => onSelectMode('enterprise')}
          className="w-full p-5 bg-[#12141c] border border-gray-950 hover:border-purple-900/30 rounded-2xl flex items-center justify-between transition-all group"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-[#0b0c10] rounded-xl flex items-center justify-center text-purple-400 border border-gray-950 transition-all group-hover:border-purple-600/30">
              <Building2 size={20} />
            </div>
            <div className={lang === 'ar' ? 'text-right' : 'text-left'}>
              <h3 className="text-white font-bold text-sm tracking-wide">
                {t('btnCompany')}
              </h3>
              <p className="text-gray-600 text-xs mt-0.5">
                {t('descCompany')}
              </p>
            </div>
          </div>
          <ArrowIcon 
            size={16} 
            className="text-gray-600 group-hover:text-white transition-all transform group-hover:translate-x-1 rtl:group-hover:-translate-x-1" 
          />
        </button>

        {/* OPTION 2 : NOMS DE MARQUE */}
        <button
          onClick={() => onSelectMode('brand')}
          className="w-full p-5 bg-[#12141c] border border-gray-950 hover:border-purple-900/30 rounded-2xl flex items-center justify-between transition-all group"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-[#0b0c10] rounded-xl flex items-center justify-center text-purple-400 border border-gray-950 transition-all group-hover:border-purple-600/30">
              <Tag size={20} />
            </div>
            <div className={lang === 'ar' ? 'text-right' : 'text-left'}>
              <h3 className="text-white font-bold text-sm tracking-wide">
                {t('btnBrand')}
              </h3>
              <p className="text-gray-600 text-xs mt-0.5">
                {t('descBrand')}
              </p>
            </div>
          </div>
          <ArrowIcon 
            size={16} 
            className="text-gray-600 group-hover:text-white transition-all transform group-hover:translate-x-1 rtl:group-hover:-translate-x-1" 
          />
        </button>

      </div>
    </div>
  );
}
