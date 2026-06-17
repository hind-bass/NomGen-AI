import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Sparkles, Globe, Eye, EyeOff, Lock, Mail, ArrowLeft, ArrowRight } from 'lucide-react';

export default function AuthScreen({ onAuthSuccess }) {
  const { lang, setLang } = useApp();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  // États pour afficher/masquer le mot de passe (Œil)
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const API_BASE = 'http://127.0.0.1:8000';

  // Gestion de la flèche de retour selon le sens de lecture (LTR / RTL)
  const BackIcon = lang === 'ar' ? ArrowRight : ArrowLeft;

  // Traductions locales dédiées à l'authentification
  const authTranslations = {
    fr: {
      loginTitle: "Connexion",
      registerTitle: "Créer un compte",
      subtitle: "Accédez à l'univers créatif de BrandForge",
      emailLabel: "Adresse e-mail",
      passLabel: "Mot de passe",
      confirmPassLabel: "Confirmer le mot de passe",
      btnSubmitLogin: "Se connecter",
      btnSubmitRegister: "S'inscrire",
      switchtoRegister: "Nouveau ici ? Créez un compte",
      switchtoLogin: "Déjà membre ? Connectez-vous",
      errFields: "Veuillez remplir tous les champs.",
      errMatch: "Les mots de passe ne correspondent pas.",
      errAuth: "Email ou mot de passe incorrect.",
      errNetwork: "Impossible de joindre le serveur.",
      errRegister: "Impossible de créer le compte.",
    },
    ar: {
      loginTitle: "تسجيل الدخول",
      registerTitle: "إنشاء حساب جديد",
      subtitle: "ابدأ رحلتك الإبداعية مع BrandForge",
      emailLabel: "البريد الإلكتروني",
      passLabel: "كلمة المرور",
      confirmPassLabel: "تأكيد كلمة المرور",
      btnSubmitLogin: "تسجيل الدخول",
      btnSubmitRegister: "إنشاء الحساب",
      switchtoRegister: "جديد هنا؟ أنشئ حساباً جديداً",
      switchtoLogin: "عضو بالفعل؟ سجل دخولك",
      errFields: "يرجى ملء جميع الحقول.",
      errMatch: "كلمات المرور غير متطابقة.",
      errAuth: "البريد الإلكتروني أو كلمة المرور غير صحيحة.",
      errNetwork: "تعذر الاتصال بالخادم.",
      errRegister: "تعذر إنشاء الحساب.",
    }
  };

  const at = (key) => authTranslations[lang][key] || key;

  const resetForm = () => {
    setError('');
    setShowPassword(false);
    setShowConfirmPassword(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email || !password || (isRegister && !confirmPassword)) {
      setError(at('errFields'));
      return;
    }

    if (isRegister && password !== confirmPassword) {
      setError(at('errMatch'));
      return;
    }

    setIsLoading(true);
    try {
      if (isRegister) {
        const regRes = await fetch(`${API_BASE}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
        if (!regRes.ok) {
          const data = await regRes.json().catch(() => ({}));
          setError(data.detail || at('errRegister'));
          return;
        }
      }

      const loginRes = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!loginRes.ok) {
        setError(at('errAuth'));
        return;
      }

      const data = await loginRes.json();
      onAuthSuccess({ email: data.email, role: data.role }, data.access_token);
    } catch {
      setError(at('errNetwork'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0c10] text-white flex flex-col relative animate-fade-in">
      
      {/* EN-HAUT : BARRE D'OUTILS (SÉLECTEUR DE LANGUE) */}
      <header className="w-full px-8 py-4 flex justify-end items-center absolute top-0 left-0 right-0 z-50">
        <button 
          onClick={() => setLang(lang === 'fr' ? 'ar' : 'fr')}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#12141c] border border-gray-950 text-xs font-semibold rounded-full hover:text-purple-400 hover:border-purple-600/30 transition-all shadow-md"
        >
          <Globe size={13} />
          <span className="uppercase">{lang}</span>
        </button>
      </header>

      {/* ZONE CENTRALE DU FORMULAIRE */}
      <div className="flex-1 flex items-center justify-center px-4 py-16">
        <div className="w-full max-w-md bg-[#12141c] border border-gray-950 rounded-2xl p-8 shadow-2xl relative">
          
          {/* ⚡ BOUTON RETOUR EN ARRIÈRE (Visible uniquement en mode inscription) */}
          {isRegister && (
            <button
              type="button"
              onClick={() => {
                setIsRegister(false);
                resetForm();
              }}
              className={`absolute top-6 bg-[#0b0c10] border border-gray-900 p-2 rounded-xl text-gray-500 hover:text-white hover:border-purple-600/30 transition-all active:scale-95 flex items-center justify-center ${
                lang === 'ar' ? 'left-6' : 'right-6'
              }`}
            >
              <BackIcon size={14} />
            </button>
          )}

          {/* LOGO */}
          <div className="flex flex-col items-center gap-3 text-center mb-8">
            <div className="w-12 h-12 bg-gradient-to-tr from-purple-600 to-indigo-500 rounded-xl flex items-center justify-center shadow-lg shadow-purple-900/20">
              <Sparkles size={22} className="text-white" />
            </div>
            <h1 className="text-2xl font-bold tracking-wider">BrandForge</h1>
            <p className="text-gray-500 text-xs max-w-xs">{at('subtitle')}</p>
          </div>

          {/* MESSAGE D'ERREUR */}
          {error && (
            <div className={`p-3 bg-red-950/20 border border-red-900/40 text-red-400 rounded-xl text-xs font-medium mb-5 ${lang === 'ar' ? 'text-right' : 'text-left'}`}>
              ⚠️ {error}
            </div>
          )}

          {/* FORMULAIRE */}
          <form onSubmit={handleSubmit} className="space-y-4">
            
            {/* INPUT EMAIL */}
            <div className="flex flex-col gap-1.5">
              <label className={`text-[10px] text-gray-500 font-semibold uppercase tracking-wide ${lang === 'ar' ? 'text-right' : 'text-left'}`}>
                {at('emailLabel')}
              </label>
              <div className="relative flex items-center">
                <span className={`absolute text-gray-600 ${lang === 'ar' ? 'right-4' : 'left-4'}`}>
                  <Mail size={14} />
                </span>
                <input 
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className={`w-full py-3 bg-[#0b0c10] border border-gray-900 focus:border-purple-600/50 rounded-xl text-xs text-white placeholder-gray-700 outline-none transition-all ${
                    lang === 'ar' ? 'pr-11 pl-4 text-right' : 'pl-11 pr-4 text-left'
                  }`}
                />
              </div>
            </div>

            {/* INPUT MOT DE PASSE AVEC L'ŒIL */}
            <div className="flex flex-col gap-1.5">
              <label className={`text-[10px] text-gray-500 font-semibold uppercase tracking-wide ${lang === 'ar' ? 'text-right' : 'text-left'}`}>
                {at('passLabel')}
              </label>
              <div className="relative flex items-center">
                <span className={`absolute text-gray-600 ${lang === 'ar' ? 'right-4' : 'left-4'}`}>
                  <Lock size={14} />
                </span>
                <input 
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className={`w-full py-3 bg-[#0b0c10] border border-gray-900 focus:border-purple-600/50 rounded-xl text-xs text-white placeholder-gray-700 outline-none transition-all ${
                    lang === 'ar' ? 'pr-11 pl-12 text-right' : 'pl-11 pr-12 text-left'
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className={`absolute text-gray-600 hover:text-purple-400 transition-colors ${lang === 'ar' ? 'left-4' : 'right-4'}`}
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            {/* INPUT CONFIRMATION MOT DE PASSE AVEC L'ŒIL (VISIBLE SEULEMENT EN INSCRIPTION) */}
            {isRegister && (
              <div className="flex flex-col gap-1.5 animate-fade-in">
                <label className={`text-[10px] text-gray-500 font-semibold uppercase tracking-wide ${lang === 'ar' ? 'text-right' : 'text-left'}`}>
                  {at('confirmPassLabel')}
                </label>
                <div className="relative flex items-center">
                  <span className={`absolute text-gray-600 ${lang === 'ar' ? 'right-4' : 'left-4'}`}>
                    <Lock size={14} />
                  </span>
                  <input 
                    type={showConfirmPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    className={`w-full py-3 bg-[#0b0c10] border border-gray-900 focus:border-purple-600/50 rounded-xl text-xs text-white placeholder-gray-700 outline-none transition-all ${
                      lang === 'ar' ? 'pr-11 pl-12 text-right' : 'pl-11 pr-12 text-left'
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className={`absolute text-gray-600 hover:text-purple-400 transition-colors ${lang === 'ar' ? 'left-4' : 'right-4'}`}
                  >
                    {showConfirmPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>
            )}

            {/* BOUTON SOUMISSION PRINCIPAL */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 mt-4 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-bold rounded-xl text-xs tracking-wide transition-all shadow-lg shadow-purple-950/30 active:scale-[0.98]"
            >
              {isLoading ? '...' : (isRegister ? at('btnSubmitRegister') : at('btnSubmitLogin'))}
            </button>
          </form>

          {/* LIEN DE BASCULEMENT (Se connecter / Créer un compte) */}
        {!isRegister && (
          <div className="mt-6 text-center">
            <span className="text-xs text-gray-500">
              {lang === 'ar' ? 'ليس لديك حساب؟ ' : 'Nouveau sur BrandForge ? '}
            </span>
            <button
              onClick={() => { setIsRegister(true); setError(''); }}
              className="text-xs text-purple-400 font-bold hover:underline transition-all"
            >
              {lang === 'ar' ? 'أنشئ حساباً الآن' : 'Créer un compte'}
            </button>
          </div>
        )}

        </div>
      </div>

    </div>
  );
}