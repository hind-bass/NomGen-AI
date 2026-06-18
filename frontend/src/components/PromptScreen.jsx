import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { ArrowLeft, ArrowRight, Sparkles, Cpu, Layers, Loader2 } from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

export default function PromptScreen({ generationType, onGoBack, onGenerate }) {
  const { lang, t } = useApp();
  const [prompt, setPrompt] = useState('');
  const [selectedStyle, setSelectedStyle] = useState('Tous');
  const [isModeB, setIsModeB] = useState(false);
  const [error, setError] = useState('');

  const [llmModels, setLlmModels] = useState([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('');

  const BackIcon = lang === 'ar' ? ArrowRight : ArrowLeft;
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
      modelLoading: "Chargement des modèles...",
      modelUnavailable: "Non disponible — voir la configuration ci-dessous",
      modelLocal: "Local (Ollama)",
      modelSetupHint: "Pour activer les modèles locaux : lancez Ollama puis « ollama pull mistral »",
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
      modelLoading: "جاري تحميل النماذج...",
      modelUnavailable: "غير متاح — راجع الإعدادات أدناه",
      modelLocal: "محلي (Ollama)",
      modelSetupHint: "لتفعيل النماذج المحلية: شغّل Ollama ثم « ollama pull mistral »",
      btnGenerate: "توليد المقترحات",
      errorPrompt: "يرجى كتابة وصف المشروع قبل المتابعة.",
      tous: "الكل",
      tech: "تقنية",
      food: "طعام",
      luxe: "فخامة"
    }
  };

  const lt = (key) => localTranslations[lang][key] || key;

  // Charger les modèles LLM depuis l'API backend
  useEffect(() => {
    if (!isModeB) return;

    async function fetchModels() {
      setModelsLoading(true);
      try {
        const response = await fetch(`${API_BASE}/api/models/llm-list?langue=${lang}`);
        if (response.ok) {
          const data = await response.json();
          const models = data.models || [];
          setLlmModels(models);
          const firstAvailable = models.find((m) => m.available) || models[0];
          if (firstAvailable) setSelectedModel(firstAvailable.key);
        }
      } catch (err) {
        console.error('Erreur chargement modèles LLM:', err);
      } finally {
        setModelsLoading(false);
      }
    }
    fetchModels();
  }, [lang, isModeB]);

  // Réinitialiser les erreurs et le prompt si on bascule entre les modes
  React.useEffect(() => {
    setError('');
    if (!isModeB) setPrompt('');
  }, [isModeB]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    // La validation du prompt s'applique UNIQUEMENT en Mode B
    if (isModeB && !prompt.trim()) {
      setError(lt('errorPrompt'));
      return;
    }

    if (isModeB && !selectedModel) {
      setError(lt('modelLoading'));
      return;
    }

    const selected = llmModels.find((m) => m.key === selectedModel);
    if (isModeB && selected && !selected.available) {
      setError(selected.unavailable_reason || lt('modelUnavailable'));
      return;
    }

    onGenerate({
      prompt: isModeB ? prompt.trim() : '',
      mode: isModeB ? 'B' : 'A',
      model: isModeB ? selectedModel : 'nanoGPT',
      modelLabel: llmModels.find((m) => m.key === selectedModel)?.nom_affiche || selectedModel,
      style: selectedStyle,
      generationType,
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

          {/* INPUT DESCRIPTION PROMPT - RENDU CONDITIONNEL (UNIQUEMENT MODE B) */}
          {isModeB && (
            <div className="flex flex-col gap-1.5 animate-fade-in">
              <label className={`text-[10px] text-gray-500 font-semibold uppercase tracking-wide ${lang === 'ar' ? 'text-right' : 'text-left'}`}>
                {lt('labelPrompt')}
              </label>
              <textarea
                value={prompt}
                onChange={(e) => {
                  setPrompt(e.target.value);
                  if (e.target.value.trim()) setError(''); 
                }}
                placeholder={lt('placeholderPrompt')}
                rows={4}
                className={`w-full p-4 bg-[#0b0c10] border border-gray-900 focus:border-purple-600/50 rounded-xl text-xs text-white placeholder-gray-700 outline-none transition-all resize-none leading-relaxed ${
                  lang === 'ar' ? 'text-right' : 'text-left'
                }`}
              />
            </div>
          )}

          {/* ⚡ BARRE DE CHOIX DU STYLE (Toujours visible pour filtrer) */}
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
              {modelsLoading ? (
                <div className="flex items-center gap-2 text-gray-500 text-xs py-2">
                  <Loader2 size={14} className="animate-spin text-purple-500" />
                  {lt('modelLoading')}
                </div>
              ) : (
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className={`w-full p-3 bg-[#0b0c10] border border-gray-900 focus:border-purple-600/50 rounded-xl text-xs text-white outline-none transition-all cursor-pointer ${
                    lang === 'ar' ? 'text-right' : 'text-left'
                  }`}
                >
                  {llmModels.map((model) => (
                    <option
                      key={model.key}
                      value={model.key}
                      disabled={!model.available}
                      className="bg-[#12141c]"
                    >
                      {model.nom_affiche}
                      {model.env_required?.length === 0 ? ` — ${lt('modelLocal')}` : ''}
                      {!model.available ? ' ⚠' : ''}
                    </option>
                  ))}
                </select>
              )}
              {selectedModel && llmModels.find((m) => m.key === selectedModel) && (
                <p className={`text-[10px] mt-1 ${llmModels.find((m) => m.key === selectedModel).available ? 'text-gray-600' : 'text-amber-500/80'}`}>
                  {llmModels.find((m) => m.key === selectedModel).description}
                  {!llmModels.find((m) => m.key === selectedModel).available && (
                    <span className="block mt-0.5">
                      {llmModels.find((m) => m.key === selectedModel).unavailable_reason || lt('modelUnavailable')}
                    </span>
                  )}
                </p>
              )}
              {llmModels.length > 0 && !llmModels.some((m) => m.available) && (
                <p className="text-[10px] text-amber-500/80 mt-2">{lt('modelSetupHint')}</p>
              )}
            </div>
          )}

          {/* ⚡ INTERFACE : MESSAGE D'ERREUR TEXTUEL INTÉGRÉ (S'AFFICHERA SEULEMENT EN MODE B SI VIDE) */}
          {error && isModeB && (
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
