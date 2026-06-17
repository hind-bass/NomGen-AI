import React, { useState, useEffect, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import {
  Check, X, ArrowLeft, Loader2, Users, MessageSquare,
  UserPlus, Shield, ShieldOff, Trash2, ToggleLeft, ToggleRight
} from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

export default function AdminDashboard({ onGoBack }) {
  const { lang, token, user: currentUser } = useApp();
  const [activeTab, setActiveTab] = useState('moderation');

  const [suggestions, setSuggestions] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createForm, setCreateForm] = useState({ email: '', password: '', role: 'user', is_active: true });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const t = (fr, ar) => (lang === 'ar' ? ar : fr);

  const showMessage = (msg) => {
    setMessage(msg);
    setTimeout(() => setMessage(''), 2500);
  };

  const authHeaders = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  const fetchSuggestions = useCallback(async () => {
    const response = await fetch(`${API_BASE}/api/suggestions`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (response.ok) {
      const data = await response.json();
      setSuggestions(data.filter((s) => s.status === 'pending') || []);
    }
  }, [token]);

  const fetchUsers = useCallback(async () => {
    const response = await fetch(`${API_BASE}/api/admin/users`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (response.ok) {
      setUsers(await response.json());
    }
  }, [token]);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        await Promise.all([fetchSuggestions(), fetchUsers()]);
      } catch (error) {
        console.error('Erreur de chargement admin:', error);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [fetchSuggestions, fetchUsers]);

  const handleModerate = async (id, action) => {
    try {
      const response = await fetch(`${API_BASE}/api/suggestions/${id}/${action}`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        setSuggestions((prev) => prev.filter((item) => item.id !== id));
        showMessage(
          action === 'approve'
            ? t('Suggestion approuvée et intégrée !', 'تم قبول الاقتراح وإضافته!')
            : t('Suggestion rejetée.', 'تم رفض الاقتراح.')
        );
      }
    } catch (error) {
      console.error('Erreur modération:', error);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}/api/admin/users`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify(createForm),
      });
      if (response.ok) {
        const newUser = await response.json();
        setUsers((prev) => [...prev, newUser]);
        setCreateForm({ email: '', password: '', role: 'user', is_active: true });
        setCreateModalOpen(false);
        showMessage(t('Utilisateur créé avec succès.', 'تم إنشاء المستخدم بنجاح.'));
      } else {
        const data = await response.json().catch(() => ({}));
        showMessage(data.detail || t('Erreur lors de la création.', 'خطأ أثناء الإنشاء.'));
      }
    } catch {
      showMessage(t('Impossible de joindre le serveur.', 'تعذر الاتصال بالخادم.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateUser = async (userId, updates) => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/users/${userId}`, {
        method: 'PATCH',
        headers: authHeaders,
        body: JSON.stringify(updates),
      });
      if (response.ok) {
        const updated = await response.json();
        setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
        showMessage(t('Utilisateur mis à jour.', 'تم تحديث المستخدم.'));
      } else {
        const data = await response.json().catch(() => ({}));
        showMessage(data.detail || t('Erreur lors de la mise à jour.', 'خطأ أثناء التحديث.'));
      }
    } catch {
      showMessage(t('Impossible de joindre le serveur.', 'تعذر الاتصال بالخادم.'));
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm(t('Supprimer cet utilisateur ?', 'حذف هذا المستخدم؟'))) return;
    try {
      const response = await fetch(`${API_BASE}/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        setUsers((prev) => prev.filter((u) => u.id !== userId));
        showMessage(t('Utilisateur supprimé.', 'تم حذف المستخدم.'));
      } else {
        const data = await response.json().catch(() => ({}));
        showMessage(data.detail || t('Erreur lors de la suppression.', 'خطأ أثناء الحذف.'));
      }
    } catch {
      showMessage(t('Impossible de joindre le serveur.', 'تعذر الاتصال بالخادم.'));
    }
  };

  const formatDate = (iso) => {
    try {
      return new Date(iso).toLocaleDateString(lang === 'ar' ? 'ar-MA' : 'fr-FR', {
        day: '2-digit', month: 'short', year: 'numeric',
      });
    } catch {
      return iso;
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-gray-400 gap-3">
        <Loader2 className="animate-spin text-purple-500" size={32} />
        <p className="text-xs">{t('Chargement du dashboard admin...', 'جاري تحميل لوحة التحكم...')}</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 text-white animate-fade-in">

      {/* EN-TÊTE */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-gray-900 pb-6 mb-6">
        <div>
          <h1 className="text-xl font-bold tracking-wide flex items-center gap-2">
            <Users size={20} className="text-purple-500" />
            {t('Dashboard Administrateur', 'لوحة تحكم المشرف')}
          </h1>
          <p className="text-xs text-gray-500 mt-1">
            {t('Modérez les suggestions et gérez les comptes utilisateurs.', 'راجع الاقتراحات وأدر حسابات المستخدمين.')}
          </p>
        </div>
        <button
          onClick={onGoBack}
          className="flex items-center gap-2 px-4 py-2 bg-[#12141c] hover:bg-gray-900 border border-gray-800 rounded-xl text-xs font-semibold text-gray-400 hover:text-white transition-all active:scale-95"
        >
          <ArrowLeft size={14} />
          <span>{t('Retour à l\'accueil', 'رجوع للرئيسية')}</span>
        </button>
      </div>

      {/* ONGLETS */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('moderation')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'moderation'
              ? 'bg-purple-600 text-white shadow-lg shadow-purple-950/30'
              : 'bg-[#12141c] text-gray-400 border border-gray-900 hover:text-white'
          }`}
        >
          <MessageSquare size={14} />
          {t('Modération', 'المراجعة')}
          {suggestions.length > 0 && (
            <span className="bg-purple-950/60 text-purple-300 px-1.5 py-0.5 rounded-full text-[10px]">
              {suggestions.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('users')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'users'
              ? 'bg-purple-600 text-white shadow-lg shadow-purple-950/30'
              : 'bg-[#12141c] text-gray-400 border border-gray-900 hover:text-white'
          }`}
        >
          <Users size={14} />
          {t('Utilisateurs', 'المستخدمون')}
          <span className="bg-purple-950/60 text-purple-300 px-1.5 py-0.5 rounded-full text-[10px]">
            {users.length}
          </span>
        </button>
      </div>

      {/* TOAST */}
      {message && (
        <div className="mb-4 text-center text-xs font-medium py-2.5 px-4 bg-purple-950/40 text-purple-300 border border-purple-900/40 rounded-xl animate-fade-in">
          {message}
        </div>
      )}

      {/* ── ONGLET MODÉRATION ── */}
      {activeTab === 'moderation' && (
        <div className="bg-[#12141c] border border-gray-900 rounded-2xl overflow-hidden shadow-xl">
          {suggestions.length === 0 ? (
            <div className="text-center py-16 text-gray-600 text-xs space-y-2">
              <p className="text-3xl">☕</p>
              <p>{t('Aucune suggestion en attente pour le moment.', 'لا توجد اقتراحات معلقة حالياً.')}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-gray-900 text-gray-500 font-bold text-[10px] tracking-wider uppercase bg-[#161922]/50">
                    <th className="p-4">{t('Nom suggéré', 'الاسم المقترح')}</th>
                    <th className="p-4">{t('Catégorie', 'التصنيف')}</th>
                    <th className="p-4">{t('Langue', 'اللغة')}</th>
                    <th className="p-4 text-center w-32">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-900/60 text-xs font-medium">
                  {suggestions.map((item) => (
                    <tr key={item.id} className="hover:bg-[#161922]/30 transition-all">
                      <td className="p-4 font-bold text-white tracking-wide">{item.nom}</td>
                      <td className="p-4">
                        <span className="bg-gray-900 border border-gray-800 text-gray-400 px-2 py-0.5 rounded-md text-[10px] uppercase font-bold">
                          {item.categorie}
                        </span>
                      </td>
                      <td className="p-4 text-gray-400 uppercase">{item.langue}</td>
                      <td className="p-4">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => handleModerate(item.id, 'approve')}
                            className="w-8 h-8 rounded-lg bg-emerald-950/40 text-emerald-400 border border-emerald-900/30 flex items-center justify-center hover:bg-emerald-600 hover:text-white transition-all active:scale-95"
                            title={t('Approuver', 'قبول')}
                          >
                            <Check size={14} />
                          </button>
                          <button
                            onClick={() => handleModerate(item.id, 'reject')}
                            className="w-8 h-8 rounded-lg bg-red-950/40 text-red-400 border border-red-900/30 flex items-center justify-center hover:bg-red-600 hover:text-white transition-all active:scale-95"
                            title={t('Rejeter', 'رفض')}
                          >
                            <X size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── ONGLET UTILISATEURS ── */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={() => setCreateModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-xl text-xs transition-all active:scale-95 shadow-lg shadow-purple-950/30"
            >
              <UserPlus size={14} />
              {t('Créer un utilisateur', 'إنشاء مستخدم')}
            </button>
          </div>

          <div className="bg-[#12141c] border border-gray-900 rounded-2xl overflow-hidden shadow-xl">
            {users.length === 0 ? (
              <div className="text-center py-16 text-gray-600 text-xs space-y-2">
                <p className="text-3xl">👤</p>
                <p>{t('Aucun utilisateur enregistré.', 'لا يوجد مستخدمون.')}</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-gray-900 text-gray-500 font-bold text-[10px] tracking-wider uppercase bg-[#161922]/50">
                      <th className="p-4">{t('Email', 'البريد')}</th>
                      <th className="p-4">{t('Rôle', 'الدور')}</th>
                      <th className="p-4">{t('Statut', 'الحالة')}</th>
                      <th className="p-4">{t('Créé le', 'تاريخ الإنشاء')}</th>
                      <th className="p-4 text-center w-36">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-900/60 text-xs font-medium">
                    {users.map((u) => {
                      const isSelf = u.email === currentUser?.email;
                      return (
                        <tr key={u.id} className="hover:bg-[#161922]/30 transition-all">
                          <td className="p-4">
                            <span className="font-bold text-white">{u.email}</span>
                            {isSelf && (
                              <span className="ml-2 text-[10px] text-purple-400 font-bold">(vous)</span>
                            )}
                          </td>
                          <td className="p-4">
                            <span className={`px-2 py-0.5 rounded-md text-[10px] uppercase font-bold border ${
                              u.role === 'admin'
                                ? 'bg-purple-950/40 text-purple-400 border-purple-900/30'
                                : 'bg-gray-900 text-gray-400 border-gray-800'
                            }`}>
                              {u.role}
                            </span>
                          </td>
                          <td className="p-4">
                            <span className={`px-2 py-0.5 rounded-md text-[10px] uppercase font-bold border ${
                              u.is_active
                                ? 'bg-emerald-950/40 text-emerald-400 border-emerald-900/30'
                                : 'bg-red-950/40 text-red-400 border-red-900/30'
                            }`}>
                              {u.is_active ? t('Actif', 'نشط') : t('Inactif', 'معطل')}
                            </span>
                          </td>
                          <td className="p-4 text-gray-500">{formatDate(u.created_at)}</td>
                          <td className="p-4">
                            <div className="flex items-center justify-center gap-1.5">
                              <button
                                onClick={() => handleUpdateUser(u.id, { role: u.role === 'admin' ? 'user' : 'admin' })}
                                disabled={isSelf}
                                className="w-8 h-8 rounded-lg bg-purple-950/40 text-purple-400 border border-purple-900/30 flex items-center justify-center hover:bg-purple-600 hover:text-white transition-all active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed"
                                title={u.role === 'admin' ? t('Rétrograder', 'إزالة صلاحية المشرف') : t('Promouvoir admin', 'ترقية لمشرف')}
                              >
                                {u.role === 'admin' ? <ShieldOff size={14} /> : <Shield size={14} />}
                              </button>
                              <button
                                onClick={() => handleUpdateUser(u.id, { is_active: !u.is_active })}
                                disabled={isSelf}
                                className="w-8 h-8 rounded-lg bg-blue-950/40 text-blue-400 border border-blue-900/30 flex items-center justify-center hover:bg-blue-600 hover:text-white transition-all active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed"
                                title={u.is_active ? t('Désactiver', 'تعطيل') : t('Activer', 'تفعيل')}
                              >
                                {u.is_active ? <ToggleRight size={14} /> : <ToggleLeft size={14} />}
                              </button>
                              <button
                                onClick={() => handleDeleteUser(u.id)}
                                disabled={isSelf}
                                className="w-8 h-8 rounded-lg bg-red-950/40 text-red-400 border border-red-900/30 flex items-center justify-center hover:bg-red-600 hover:text-white transition-all active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed"
                                title={t('Supprimer', 'حذف')}
                              >
                                <Trash2 size={14} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* MODALE CRÉATION UTILISATEUR */}
      {createModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-[#12141c] border border-purple-900/30 rounded-3xl p-6 max-w-md w-full text-white shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-gray-900 pb-3">
              <h3 className="text-sm font-bold text-purple-400 flex items-center gap-2">
                <UserPlus size={16} />
                {t('Créer un utilisateur', 'إنشاء مستخدم')}
              </h3>
              <button
                onClick={() => setCreateModalOpen(false)}
                className="text-gray-500 hover:text-white font-bold text-lg bg-[#1f2833]/40 w-8 h-8 rounded-full flex items-center justify-center"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreateUser} className="space-y-4 text-xs">
              <div className="flex flex-col gap-1.5">
                <label className="text-gray-400">{t('Adresse e-mail', 'البريد الإلكتروني')}</label>
                <input
                  type="email"
                  required
                  value={createForm.email}
                  onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                  placeholder="user@example.com"
                  className="w-full bg-[#1f2833]/40 border border-gray-800 rounded-xl p-2.5 text-white focus:border-purple-500 outline-none"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-gray-400">{t('Mot de passe', 'كلمة المرور')}</label>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={createForm.password}
                  onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
                  placeholder="••••••••"
                  className="w-full bg-[#1f2833]/40 border border-gray-800 rounded-xl p-2.5 text-white focus:border-purple-500 outline-none"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-gray-400">{t('Rôle', 'الدور')}</label>
                <select
                  value={createForm.role}
                  onChange={(e) => setCreateForm({ ...createForm, role: e.target.value })}
                  className="w-full bg-[#1f2833] border border-gray-800 rounded-xl p-2.5 text-white focus:border-purple-500 outline-none"
                >
                  <option value="user">{t('Utilisateur', 'مستخدم')}</option>
                  <option value="admin">{t('Administrateur', 'مشرف')}</option>
                </select>
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={createForm.is_active}
                  onChange={(e) => setCreateForm({ ...createForm, is_active: e.target.checked })}
                  className="accent-purple-600"
                />
                <span className="text-gray-400">{t('Compte actif', 'حساب نشط')}</span>
              </label>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setCreateModalOpen(false)}
                  className="flex-1 py-2.5 bg-gray-900 text-gray-400 font-bold rounded-xl hover:bg-gray-800 transition-all"
                >
                  {t('Annuler', 'إلغاء')}
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 py-2.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-60 text-white font-bold rounded-xl transition-all"
                >
                  {isSubmitting ? '...' : t('Créer', 'إنشاء')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
