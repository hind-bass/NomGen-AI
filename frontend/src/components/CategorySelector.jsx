import React from 'react';
import { useApp } from '../context/AppContext';

export function CategorySelector({ type, onSelectCategory }) {
  const { lang, categories } = useApp();

  if (!categories) {
    return <div className="p-8 text-center text-gray-500">Loading categories...</div>;
  }

  const typeConfig = categories.categories[type];
  if (!typeConfig) {
    return <div className="p-8 text-center text-red-500">Invalid type: {type}</div>;
  }

  const sectors = typeConfig.sectors;

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center p-8 bg-[#0b0c10] animate-fade-in">
      <div className="w-full max-w-2xl">

        {/* HAUT : Titre et sous-titre */}
        <div className="mb-12 text-center">
          <h1 className="text-4xl font-bold text-white mb-2 tracking-tight">
            {typeConfig[`label_${lang}`]}
          </h1>
          <p className="text-gray-400 text-sm md:text-base">
            {lang === 'fr' ? 'Sélectionnez une catégorie' : 'اختر فئة'}
          </p>
        </div>

        {/* GRILLE DE CATÉGORIES */}
        <div className="grid grid-cols-2 gap-4 mb-8">
          {sectors.map((sector) => (
            <button
              key={sector.id}
              onClick={() => onSelectCategory(type, sector.id)}
              className="p-6 bg-[#12141c] hover:bg-[#1a1d29] rounded-xl border border-gray-950 hover:border-purple-900 transition-all duration-300 group"
            >
              <div className="text-center">
                <h2 className="text-lg font-semibold text-white mb-2 group-hover:text-purple-400 transition-colors">
                  {sector[`label_${lang}`]}
                </h2>
                <p className="text-xs text-gray-500 group-hover:text-gray-400 transition-colors">
                  {sector[`description_${lang}`] || ''}
                </p>
              </div>
            </button>
          ))}
        </div>

        {/* BOUTON RETOUR */}
        <button
          onClick={() => onSelectCategory(null, null)}
          className="w-full py-3 px-4 bg-[#12141c] hover:bg-[#1a1d29] border border-gray-950 hover:border-purple-900 text-white font-semibold rounded-xl transition-all duration-300"
        >
          {lang === 'fr' ? '← Retour' : '← رجوع'}
        </button>
      </div>
    </div>
  );
}
