import React from 'react';
import { useApp } from '../context/AppContext';

export default function BrandCard({ data, animationClass, index, config }) {
  // ⚡ MISE À JOUR : Extraction de la fonction de traduction 't' depuis le contexte
  const { lang, t } = useApp();

  if (!data) return null;

  // Liste de dégradés élégants et colorés (Violet, Rouge/Orange, Bleu/Teal, Vert, Rose/Jaune)
  const gradients = [
    "from-purple-600 via-indigo-700 to-purple-900 border-purple-400/30",
    "from-red-600 via-orange-600 to-yellow-700 border-orange-400/30",
    "from-blue-600 via-cyan-600 to-indigo-800 border-blue-400/30",
    "from-emerald-600 via-teal-600 to-green-800 border-emerald-400/30",
    "from-pink-600 via-rose-600 to-purple-800 border-rose-400/30"
  ];

  // Sélectionne une couleur de manière circulaire selon l'index de la carte
  const currentGradient = gradients[index % gradients.length];

  // ⚡ LOGIQUE SÉCURISÉE DE TRADUCTION DU STYLE
  // Récupère la valeur brute du style (depuis l'élément ou la configuration globale)
  const rawStyle = data.style || data.secteur || config?.style || "tech";
  // Nettoie et traduit la valeur de manière dynamique
  const translatedStyle = t(rawStyle.toLowerCase().trim());

  return (
    <div className={`w-full max-w-sm aspect-[3/4] rounded-3xl p-8 flex flex-col justify-between relative overflow-hidden shadow-2xl transition-all duration-500 bg-gradient-to-br ${currentGradient} border ${animationClass}`}>
      
      {/* EFFET GRAPHIQUE EN ARRIÈRE-PLAN */}
      <div className="absolute inset-0 bg-black/10 backdrop-blur-[1px] z-0" />
      <div className="absolute -bottom-10 -right-10 text-9xl font-black text-white/5 uppercase select-none z-0 tracking-tighter">
        {translatedStyle}
      </div>

      {/* METADONNÉES EN HAUT */}
      <div className="z-10 flex flex-col gap-1 items-start">
        {/* ⚡ RÉPARATION : Remplacement du texte en dur par le style dynamique et traduit */}
        <span className="text-[10px] uppercase tracking-widest font-bold text-white/80 bg-black/20 px-3 py-1 rounded-full border border-white/10">
          {translatedStyle}
        </span>
      </div>

      {/* NOM CENTRAL DE LA MARQUE */}
      <div className="z-10 text-center flex flex-col items-center justify-center flex-1 relative">
        <h2 className="absolute text-5xl md:text-6xl font-serif font-black text-white/10 italic scale-110 select-none blur-[2px]">
          {data.nom}
        </h2>
        <h2 className="text-4xl md:text-5xl font-sans font-extrabold text-white tracking-wide drop-shadow-md relative">
          {data.nom}
        </h2>
        {data.score && (
          <p className="text-xs text-white/90 font-bold mt-3 bg-white/20 px-2 py-0.5 rounded-full">
            Score: {data.score}/100
          </p>
        )}
      </div>

      {/* ÉTOILE DE RECOMMANDATION */}
      <div className="absolute top-6 right-6 z-10 text-white/60">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
      </div>
    </div>
  );
}