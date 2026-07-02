import React, { useEffect, useState } from 'react';
import { Clock, Loader2, RotateCcw } from 'lucide-react';
import { API_BASE } from '../config/api';
import AppIcon from './AppIcon';

const SECTEUR_TO_STYLE = {
  GENERAL: 'Tous',
  TECH: 'Tech',
  FOOD: 'Food',
  LUXE: 'Luxe',
};

function formatDate(iso, lang) {
  try {
    return new Date(iso).toLocaleString(lang === 'ar' ? 'ar-MA' : 'fr-FR', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

export default function HistoryPanel({ open, onClose, token, lang, t, onRelaunch }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!open || !token) return;

    async function loadHistory() {
      setLoading(true);
      setError('');
      try {
        const response = await fetch(`${API_BASE}/api/history/?limit=50`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) {
          setError(lang === 'ar' ? 'تعذر تحميل السجل.' : 'Impossible de charger l\'historique.');
          return;
        }
        setItems(await response.json());
      } catch {
        setError(lang === 'ar' ? 'خطأ في الاتصال.' : 'Erreur de connexion.');
      } finally {
        setLoading(false);
      }
    }

    loadHistory();
  }, [open, token, lang]);

  if (!open) return null;

  return (
    <div className={`fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex ${lang === 'ar' ? 'justify-start' : 'justify-end'} animate-fade-in`}>
      <div className="flex-1" onClick={onClose} />
      <div
        className="w-full max-w-lg bg-[#12141c] h-full p-5 sm:p-6 text-white shadow-2xl flex flex-col min-h-0"
        dir={lang === 'ar' ? 'rtl' : 'ltr'}
      >
        <div className="flex justify-between items-center border-b border-gray-900 pb-3 mb-4 shrink-0">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Clock size={20} className="text-blue-400" />
            {t('historyTitle')}
          </h2>
          <button onClick={onClose} className="text-xs bg-[#1f2833] hover:bg-purple-600 px-3 py-1.5 rounded-full text-gray-300">
            {lang === 'ar' ? 'إغلاق ×' : 'Fermer ×'}
          </button>
        </div>

        <div className="flex-1 min-h-0 overflow-y-auto space-y-2.5 pr-1">
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 text-gray-500 gap-3">
              <Loader2 className="animate-spin text-purple-500" size={28} />
              <span className="text-sm">{lang === 'ar' ? 'جاري التحميل...' : 'Chargement...'}</span>
            </div>
          )}

          {!loading && error && (
            <p className="text-center text-red-400 text-sm py-8">{error}</p>
          )}

          {!loading && !error && items.length === 0 && (
            <div className="text-center py-10 text-gray-600 text-sm flex flex-col items-center gap-3">
              <AppIcon name="folderEmpty" size={36} alt="" />
              {t('noHistory')}
            </div>
          )}

          {!loading && !error && items.map((item) => (
            <div key={item.id} className="p-3.5 bg-[#1f2833]/40 border border-gray-900 rounded-xl space-y-2">
              <p className="text-white text-sm font-medium leading-snug line-clamp-2">{item.prompt}</p>
              <div className="flex flex-wrap gap-1.5 text-[10px]">
                <span className="px-2 py-0.5 rounded-full bg-purple-950/40 text-purple-300 border border-purple-900/30">
                  {item.mode === 'B' ? 'LLM' : 'nanoGPT'}
                </span>
                <span className="px-2 py-0.5 rounded-full bg-[#12141c] text-gray-400 border border-gray-900">
                  {item.secteur}
                </span>
                <span className="px-2 py-0.5 rounded-full bg-[#12141c] text-gray-400 border border-gray-900 uppercase">
                  {item.langue}
                </span>
                <span className="px-2 py-0.5 rounded-full bg-[#12141c] text-gray-400 border border-gray-900">
                  {item.n_generated} {lang === 'ar' ? 'أسماء' : 'noms'}
                </span>
              </div>
              <div className="flex justify-between items-center gap-2 pt-1">
                <span className="text-[10px] text-gray-500">{formatDate(item.created_at, lang)}</span>
                {onRelaunch && (
                  <button
                    onClick={() => onRelaunch(item)}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 bg-purple-900/30 hover:bg-purple-800/40 border border-purple-800/40 rounded-lg text-[10px] font-semibold text-purple-300 transition-all"
                  >
                    <RotateCcw size={12} />
                    {lang === 'ar' ? 'إعادة' : 'Relancer'}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
