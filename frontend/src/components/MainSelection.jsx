import React from 'react';
import { useApp } from '../context/AppContext';
import { Building2, Tag, ArrowRight, ArrowLeft } from 'lucide-react';

export default function MainSelection({ onSelectMode }) {
  const { t, lang } = useApp();

  // Flèche directionnelle dynamique selon le sens de lecture (LTR ou RTL)
  const ArrowIcon = lang === 'ar' ? ArrowLeft : ArrowRight;

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] bg-[#0b0c10] px-4">
      
      {/* SECTION TITRE */}
      <div className="text-center mb-12 animate-fade-in">
        <h1 className="text-4xl md:text-5xl font-serif font-bold text-white mb-4 tracking-tight">
          {t('title')}
        </h1>
        <p className="text-gray-400 text-sm md:text-base max-w-md mx-auto">
          {t('subtitle')}
        </p>
      </div>

      {/* BOUTONS DE SÉLECTION */}
      <div className="w-full max-w-xl flex flex-col gap-4">
        
        {/* OPTION 1 : NOMS D'ENTREPRISE */}
        <button
          onClick={() => onSelectMode('societe')}
          className="w-full flex items-center justify-between p-5 bg-[#12141c] hover:bg-[#1a1d29] border border-gray-950 hover:border-purple-900 rounded-2xl transition-all duration-300 text-right group"
        >
          <div className="flex items-center gap-4">
            <div className="p-3 bg-purple-950/50 text-purple-400 rounded-xl group-hover:bg-purple-600 group-hover:text-white transition-all">
              <Building2 size={24} />
            </div>
            <div className={`${lang === 'ar' ? 'text-right' : 'text-left'}`}>
              <h3 className="text-white font-semibold text-lg">{t('btnCompany')}</h3>
              <p className="text-gray-400 text-xs mt-0.5">{t('descCompany')}</p>
            </div>
          </div>
          <ArrowIcon size={18} className="text-gray-500 group-hover:text-purple-400 group-hover:translate-x-1 transition-all" />
        </button>

        {/* OPTION 2 : NOMS DE MARQUE */}
        <button
          onClick={() => onSelectMode('marque')}
          className="w-full flex items-center justify-between p-5 bg-[#12141c] hover:bg-[#1a1d29] border border-gray-950 hover:border-purple-900 rounded-2xl transition-all duration-300 text-right group"
        >
          <div className="flex items-center gap-4">
            <div className="p-3 bg-purple-950/50 text-purple-400 rounded-xl group-hover:bg-purple-600 group-hover:text-white transition-all">
              <Tag size={24} />
            </div>
            <div className={`${lang === 'ar' ? 'text-right' : 'text-left'}`}>
              <h3 className="text-white font-semibold text-lg">{t('btnBrand')}</h3>
              <p className="text-gray-400 text-xs mt-0.5">{t('descBrand')}</p>
            </div>
          </div>
          <ArrowIcon size={18} className="text-gray-500 group-hover:text-purple-400 group-hover:translate-x-1 transition-all" />
        </button>

      </div>
    </div>
  );
}