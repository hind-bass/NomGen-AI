import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { ArrowLeft, ArrowRight, Sparkles, Cpu, Layers } from 'lucide-react';

export default function PromptScreen({ generationType, onGoBack, onGenerate }) {
  const { lang, t } = useApp();
  const [prompt, setPrompt] = useState('');
  const [selectedStyle, setSelectedStyle] = useState('Tous'); // État pour le style sélectionné
  const [isModeB, setIsModeB] = useState(false); // false = Mode A, true = Mode B
  const [error, setError] = useState(''); // Gestion de l'erreur intégrée à l'interface
  
  // Modèles par défaut selon la langue active
  const [selectedModel, setSelectedModel] = useState(lang === 'ar' ? 'Allam' : 'Mistral');

  const BackIcon = lang === 'ar' ? ArrowRight : ArrowLeft;

  // Liste des styles disponibles
  const stylesList = ['Tous', 'Tech', 'Food', 'Luxe'];

  // Traductions locales dédiées aux nouveaux paramètres de prompt et styles
  const localTranslations = {
    fr: {
      titleEnterprise: "Créer une Entreprise",
      titleBrand: "Créer une Marque",
      labelPrompt: "Décrivez votre projet ou secteur d'activité",
      placeholderPrompt: "Ex: Une agence de tech éco-responsable axée sur l'IA...",
      labelStyle: "Choisir un style d'identité",
      modeA: "Génération Rapide (Mode A)",
      modeB: "Modèles Avancés (Mode B)",
      modelLabel: "Choisir le modèle de langage (LLM)",
      btnGenerate: "Générer les propositions",
      errorPrompt: "Veuillez saisir une description avant de continuer.",
      tous: "Tous",
      tech: "Tech",
      food: "Food",
      luxe: "Luxe"
    },
    ar: {
      titleEnterprise: "إنشاء اسم شركة",
      titleBrand: "إنشاء اسم علامة تجارية",
      labelPrompt: "صف مشروعك أو مجال عملك بدقة",
      placeholderPrompt: "مثال: وكالة تقنية صديقة للبيئة تركز على الذكاء الاصطناعي...",
      labelStyle: "اختر أسلوب الهوية",
      modeA: "توليد سريع (وضع أ)",
      modeB: "نماذج متقدمة (وضع ب)",
      modelLabel: "اختر نموذج اللغة الكبير (LLM)",
      btnGenerate: "توليد المقترحات",
      errorPrompt: "يرجى كتابة وصف المشروع قبل المتابعة.",
      tous: "الكل",
      tech: "تقنية",
      food: "طعام",
      luxe: "فخامة"
    }
  };

  const lt = (key) => localTranslations[lang][key] || key;

  // Ajuster le modèle par défaut si l'utilisateur change de langue en cours de route
  React.useEffect(() => {
    setSelectedModel(lang === 'ar' ? 'Allam' : 'Mistral');
  }, [lang]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (!prompt.trim()) {
      setError(lt('errorPrompt'));
      return;
    }

    // On transmet toutes les données de configuration configurées à CardsScreen
    onGenerate({
      prompt: prompt.trim(),
      mode: isModeB ? 'B' : 'A',
      model: isModeB ? selectedModel : 'nanoGPT',
      style: selectedStyle, // Envoie le style choisi ('Tous', 'Tech', 'Food', 'Luxe')
      generationType: generationType // Permet de savoir si on est sur 'enterprise' ou 'brand'
    });
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-[#0b0c10] text-white flex flex-col items-center justify-center px-4 py-10">
      <div className="w-full max-w-xl bg-[#12141c] border border-gray-950 rounded-2xl p-8 shadow-2xl relative animate-fade-in">
        
        {/* BOUTON RETOUR EN ARRIÈRE */}
        <button
          onClick={onGoBack}
          className={`absolute top-6 bg-[#0b0c10] border border-gray-900 p-2 rounded-xl text-gray-500 hover:text-white hover:border-purple-600/30 transition-all active:scale-95 flex items-center justify-center ${
            lang === 'ar' ? 'left-6' : 'right-6'
          }`}
        >
          <BackIcon size={14} />
        </button>

        {/* TITRE DE L'ÉCRAN */}
        <div className="mb-8 text-center">
          <span className="text-[10px] uppercase font-bold text-purple-400 bg-purple-950/40 px-3 py-1 rounded-md border border-purple-900/30 tracking-wider">
            {generationType === 'enterprise' ? 'Enterprise Mode' : 'Brand Mode'}
          </span>
          <h2 className="text-2xl font-bold tracking-tight text-white mt-3">
            {generationType === 'enterprise' ? lt('titleEnterprise') : lt('titleBrand')}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          
          {/* ⚡ PARTE 1 : TOGGLE SWITCH MODE A / MODE B */}
          <div className="bg-[#0b0c10] p-1 rounded-xl border border-gray-950 grid grid-cols-2 gap-1">
            <button
              type="button"
              onClick={() => setIsModeB(false)}
              className={`py-2.5 text-xs font-bold rounded-lg flex items-center justify-center gap-2 transition-all ${
                !isModeB 
                  ? 'bg-purple-600 text-white shadow-md shadow-purple-950/40' 
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              <Cpu size={14} />
              <span>{lt('modeA')}</span>
            </button>
            <button
              type="button"
              onClick={() => setIsModeB(true)}
              className={`py-2.5 text-xs font-bold rounded-lg flex items-center justify-center gap-2 transition-all ${
                isModeB 
                  ? 'bg-purple-600 text-white shadow-md shadow-purple-950/40' 
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              <Layers size={14} />
              <span>{lt('modeB')}</span>
            </button>
          </div>

          {/* INPUT DESCRIPTION PROMPT */}
          <div className="flex flex-col gap-1.5">
            <label className={`text-[10px] text-gray-500 font-semibold uppercase tracking-wide ${lang === 'ar' ? 'text-right' : 'text-left'}`}>
              {lt('labelPrompt')}
            </label>
            <textarea
              value={prompt}
              onChange={(e) => {
                setPrompt(e.target.value);
                if (e.target.value.trim()) setError(''); // Efface l'erreur si l'utilisateur écrit
              }}
              placeholder={lt('placeholderPrompt')}
              rows={4}
              className={`w-full p-4 bg-[#0b0c10] border border-gray-900 focus:border-purple-600/50 rounded-xl text-xs text-white placeholder-gray-700 outline-none transition-all resize-none leading-relaxed ${
                lang === 'ar' ? 'text-right' : 'text-left'
              }`}
            />
          </div>

          {/* ⚡ NOUVEAU : BARRE DE CHOIX DU STYLE (Tous, Tech, Food, Luxe) */}
          <div className="flex flex-col gap-2">
            <label className={`text-[10px] text-gray-500 font-semibold uppercase tracking-wide ${lang === 'ar' ? 'text-right' : 'text-left'}`}>
              {lt('labelStyle')}
            </label>
            <div className="flex flex-wrap gap-2 justify-start" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
              {stylesList.map((style) => (
                <button
                  key={style}
                  type="button"
                  onClick={() => setSelectedStyle(style)}
                  className={`px-4 py-2 text-xs font-medium rounded-xl border transition-all ${
                    selectedStyle === style
                      ? 'bg-purple-600/10 text-purple-400 border-purple-600/40 shadow-sm'
                      : 'bg-[#0b0c10] text-gray-400 border-gray-900 hover:text-gray-200'
                  }`}
                >
                  {lt(style.toLowerCase())}
                </button>
              ))}
            </div>
          </div>

          {/* ⚡ PARTIE 2 : SÉLECTEUR MODÈLE LLM CONDITIONNEL (VISIBLE UNIQUEMENT EN MODE B) */}
          {isModeB && (
            <div className="flex flex-col gap-1.5 p-4 bg-[#0b0c10]/50 border border-gray-900/50 rounded-xl animate-fade-in">
              <label className={`text-[10px] text-gray-500 font-semibold uppercase tracking-wide ${lang === 'ar' ? 'text-right' : 'text-left'}`}>
                {lt('modelLabel')}
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className={`w-full p-3 bg-[#0b0c10] border border-gray-900 focus:border-purple-600/50 rounded-xl text-xs text-white outline-none transition-all cursor-pointer ${
                  lang === 'ar' ? 'text-right' : 'text-left'
                }`}
              >
                {lang === 'ar' ? (
                  <>
                    <option value="Allam" className="bg-[#12141c]">Allam (علاّم - الموصى به)</option>
                    <option value="Fanar" className="bg-[#12141c]">Fanar (فنار)</option>
                  </>
                ) : (
                  <>
                    <option value="Mistral" className="bg-[#12141c]">Mistral AI (Recommended)</option>
                    <option value="Ollama" className="bg-[#12141c]">Ollama Local System</option>
                  </>
                )}
              </select>
            </div>
          )}

          {/* ⚡ INTERFACE : MESSAGE D'ERREUR TEXTUEL INTÉGRÉ */}
          {error && (
            <div className={`p-3 bg-red-950/20 border border-red-900/40 text-red-400 rounded-xl text-xs font-medium animate-fade-in ${
              lang === 'ar' ? 'text-right' : 'text-left'
            }`}>
              ⚠️ {error}
            </div>
          )}

          {/* BOUTON DE SOUMISSION */}
          <button
            type="submit"
            className="w-full py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold rounded-xl text-xs tracking-wide transition-all shadow-lg shadow-purple-950/30 active:scale-[0.98] flex items-center justify-center gap-2"
          >
            <Sparkles size={14} />
            <span>{lt('btnGenerate')}</span>
          </button>

        </form>
      </div>
    </div>
  );
}
