import React, { useState, useEffect, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import {
  Check, X, ArrowLeft, Loader2, Users, MessageSquare,
  UserPlus, Shield, ShieldOff, Trash2, ToggleLeft, ToggleRight,
  CreditCard, Clock, Search, ExternalLink, RefreshCw, CalendarPlus,
  Database, Download, Brain, BookOpen
} from 'lucide-react';
import AppIcon from './AppIcon';
import { API_BASE } from '../config/api';

export default function AdminDashboard({ onGoBack }) {
  const { lang, token, user: currentUser } = useApp();
  const [activeTab, setActiveTab] = useState('moderation');

  const [suggestions, setSuggestions] = useState([]);
  const [users, setUsers] = useState([]);
  const [reservations, setReservations] = useState([]);
  const [reservationStats, setReservationStats] = useState({ total: 0, pending: 0, paid: 0, expired: 0 });
  const [reservationFilter, setReservationFilter] = useState('');
  const [reservationSearch, setReservationSearch] = useState('');
  const [trainingStats, setTrainingStats] = useState(null);
  const [localModels, setLocalModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [finetuningGuideOpen, setFinetuningGuideOpen] = useState(false);
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
    const response = await fetch(`${API_BASE}/api/admin/suggestions?status_filter=pending`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (response.ok) {
      const data = await response.json();
      setSuggestions(data || []);
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

  const fetchReservations = useCallback(async (statusFilter = '', search = '') => {
    const params = new URLSearchParams();
    if (statusFilter) params.set('status_filter', statusFilter);
    if (search.trim()) params.set('search', search.trim());
    const qs = params.toString() ? `?${params.toString()}` : '';

    const response = await fetch(`${API_BASE}/api/admin/reservations${qs}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (response.ok) {
      setReservations(await response.json());
    }
  }, [token]);

  const fetchReservationStats = useCallback(async () => {
    const response = await fetch(`${API_BASE}/api/admin/reservations/stats`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (response.ok) {
      setReservationStats(await response.json());
    }
  }, [token]);

  const fetchTrainingStats = useCallback(async () => {
    const response = await fetch(`${API_BASE}/api/admin/training/stats`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (response.ok) {
      setTrainingStats(await response.json());
    }
  }, [token]);

  const fetchLocalModels = useCallback(async () => {
    const response = await fetch(`${API_BASE}/api/admin/training/local-models`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (response.ok) {
      const data = await response.json();
      setLocalModels(data.models || []);
    }
  }, [token]);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        await Promise.all([
          fetchSuggestions(),
          fetchUsers(),
          fetchReservations(),
          fetchReservationStats(),
          fetchTrainingStats(),
          fetchLocalModels(),
        ]);
      } catch (error) {
        console.error('Erreur de chargement admin:', error);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [fetchSuggestions, fetchUsers, fetchReservations, fetchReservationStats, fetchTrainingStats, fetchLocalModels]);

  useEffect(() => {
    if (activeTab !== 'reservations') return;
    fetchReservations(reservationFilter, reservationSearch);
  }, [activeTab, reservationFilter, reservationSearch, fetchReservations]);

  const handleModerate = async (id, action) => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/suggestions/${id}`, {
        method: 'PATCH',
        headers: authHeaders,
        body: JSON.stringify({ action }),
      });
      const data = await response.json().catch(() => ({}));
      if (response.ok) {
        setSuggestions((prev) => prev.filter((item) => item.id !== id));
        showMessage(
          action === 'approve'
            ? t('Suggestion approuvée et ajoutée au dataset !', 'تم قبول الاقتراح وإضافته!')
            : t('Suggestion rejetée.', 'تم رفض الاقتراح.')
        );
      } else {
        const detail = typeof data.detail === 'string'
          ? data.detail
          : t('Erreur lors de la modération.', 'خطأ أثناء المراجعة.');
        showMessage(detail);
        if (response.status === 409) {
          setSuggestions((prev) => prev.filter((item) => item.id !== id));
        }
      }
    } catch (error) {
      console.error('Erreur modération:', error);
      showMessage(t('Impossible de joindre le serveur.', 'تعذر الاتصال بالخادم.'));
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

  const refreshReservations = async () => {
    await Promise.all([
      fetchReservations(reservationFilter, reservationSearch),
      fetchReservationStats(),
    ]);
  };

  const handleReservationAction = async (reservationId, action, days = 30) => {
    try {
      const body = action === 'extend' ? { action, days } : { action };
      const response = await fetch(`${API_BASE}/api/admin/reservations/${reservationId}`, {
        method: 'PATCH',
        headers: authHeaders,
        body: JSON.stringify(body),
      });
      if (response.ok) {
        const updated = await response.json();
        setReservations((prev) => prev.map((r) => (r.id === reservationId ? updated : r)));
        await fetchReservationStats();
        const labels = {
          mark_paid: t('Réservation marquée comme payée.', 'تم تحديد الحجز كمدفوع.'),
          mark_unpaid: t('Paiement annulé.', 'تم إلغاء الدفع.'),
          extend: t('Expiration prolongée.', 'تم تمديد تاريخ الانتهاء.'),
        };
        showMessage(labels[action] || t('Réservation mise à jour.', 'تم تحديث الحجز.'));
      } else {
        const data = await response.json().catch(() => ({}));
        showMessage(data.detail || t('Erreur lors de la mise à jour.', 'خطأ أثناء التحديث.'));
      }
    } catch {
      showMessage(t('Impossible de joindre le serveur.', 'تعذر الاتصال بالخادم.'));
    }
  };

  const handleDeleteReservation = async (reservationId) => {
    if (!window.confirm(t('Supprimer cette réservation ?', 'حذف هذا الحجز؟'))) return;
    try {
      const response = await fetch(`${API_BASE}/api/admin/reservations/${reservationId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        setReservations((prev) => prev.filter((r) => r.id !== reservationId));
        await fetchReservationStats();
        showMessage(t('Réservation supprimée.', 'تم حذف الحجز.'));
      } else {
        const data = await response.json().catch(() => ({}));
        showMessage(data.detail || t('Erreur lors de la suppression.', 'خطأ أثناء الحذف.'));
      }
    } catch {
      showMessage(t('Impossible de joindre le serveur.', 'تعذر الاتصال بالخادم.'));
    }
  };

  const statusBadge = (status) => {
    const styles = {
      pending: 'bg-amber-950/40 text-amber-400 border-amber-900/30',
      paid: 'bg-emerald-950/40 text-emerald-400 border-emerald-900/30',
      expired: 'bg-red-950/40 text-red-400 border-red-900/30',
    };
    const labels = {
      pending: t('En attente', 'قيد الانتظار'),
      paid: t('Payée', 'مدفوعة'),
      expired: t('Expirée', 'منتهية'),
    };
    return (
      <span className={`px-2 py-0.5 rounded-md text-[10px] uppercase font-bold border ${styles[status] || styles.pending}`}>
        {labels[status] || status}
      </span>
    );
  };

  const handleExportTraining = async (format, langue = '') => {
    try {
      const params = new URLSearchParams({ format });
      if (langue) params.set('langue', langue);
      const response = await fetch(`${API_BASE}/api/admin/training/export?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        showMessage(data.detail || t('Export impossible.', 'تعذر التصدير.'));
        return;
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `nomgen_training_${langue || 'all'}.${format === 'csv' ? 'csv' : 'jsonl'}`;
      link.click();
      window.URL.revokeObjectURL(url);
      showMessage(t('Dataset exporté.', 'تم تصدير مجموعة البيانات.'));
    } catch {
      showMessage(t('Impossible de joindre le serveur.', 'تعذر الاتصال بالخادم.'));
    }
  };

  const handleSyncDatasets = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/training/sync-datasets`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        await fetchTrainingStats();
        showMessage(data.message || t('Synchronisation réussie.', 'تمت المزامنة بنجاح.'));
      } else {
        const data = await response.json().catch(() => ({}));
        showMessage(data.detail || t('Erreur de synchronisation.', 'خطأ في المزامنة.'));
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
            {t(
              'Modérez les suggestions, gérez les utilisateurs et les réservations.',
              'راجع الاقتراحات وأدر المستخدمين والحجوزات.'
            )}
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
        <button
          onClick={() => setActiveTab('reservations')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'reservations'
              ? 'bg-purple-600 text-white shadow-lg shadow-purple-950/30'
              : 'bg-[#12141c] text-gray-400 border border-gray-900 hover:text-white'
          }`}
        >
          <CreditCard size={14} />
          {t('Réservations', 'الحجوزات')}
          {reservationStats.pending > 0 && (
            <span className="bg-amber-950/60 text-amber-300 px-1.5 py-0.5 rounded-full text-[10px]">
              {reservationStats.pending}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('datasets')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'datasets'
              ? 'bg-purple-600 text-white shadow-lg shadow-purple-950/30'
              : 'bg-[#12141c] text-gray-400 border border-gray-900 hover:text-white'
          }`}
        >
          <Database size={14} />
          {t('Datasets', 'مجموعات البيانات')}
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
            <div className="text-center py-16 text-gray-600 text-xs space-y-2 flex flex-col items-center">
              <AppIcon name="coffeeEmpty" size={48} alt="" />
              <p>{t('Aucune suggestion en attente pour le moment.', 'لا توجد اقتراحات معلقة حالياً.')}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                    <tr className="border-b border-gray-900 text-gray-500 font-bold text-[10px] tracking-wider uppercase bg-[#161922]/50">
                    <th className="p-4">{t('Nom suggéré', 'الاسم المقترح')}</th>
                    <th className="p-4">{t('Type', 'النوع')}</th>
                    <th className="p-4">{t('Secteur', 'القطاع')}</th>
                    <th className="p-4">{t('Langue', 'اللغة')}</th>
                    <th className="p-4 text-center w-32">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-900/60 text-xs font-medium">
                  {suggestions.map((item) => (
                    <tr key={item.id} className="hover:bg-[#161922]/30 transition-all">
                      <td className="p-4 font-bold text-white tracking-wide">{item.nom}</td>
                      <td className="p-4">
                        <span className="bg-purple-950/40 text-purple-300 border border-purple-900/30 px-2 py-0.5 rounded-md text-[10px] uppercase font-bold">
                          {item.type_nom || 'marque'}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className="bg-gray-900 border border-gray-800 text-gray-400 px-2 py-0.5 rounded-md text-[10px] uppercase font-bold">
                          {item.secteur || item.categorie}
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
              <div className="text-center py-16 text-gray-600 text-xs space-y-2 flex flex-col items-center">
                <AppIcon name="userEmpty" size={48} alt="" />
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

      {/* ── ONGLET RÉSERVATIONS ── */}
      {activeTab === 'reservations' && (
        <div className="space-y-4">
          {/* Statistiques */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { key: 'total', label: t('Total', 'الإجمالي'), color: 'text-white', bg: 'bg-[#12141c]' },
              { key: 'pending', label: t('En attente', 'قيد الانتظار'), color: 'text-amber-400', bg: 'bg-amber-950/20' },
              { key: 'paid', label: t('Payées', 'مدفوعة'), color: 'text-emerald-400', bg: 'bg-emerald-950/20' },
              { key: 'expired', label: t('Expirées', 'منتهية'), color: 'text-red-400', bg: 'bg-red-950/20' },
            ].map(({ key, label, color, bg }) => (
              <div key={key} className={`${bg} border border-gray-900 rounded-xl p-4 text-center`}>
                <p className={`text-2xl font-black ${color}`}>{reservationStats[key] ?? 0}</p>
                <p className="text-[10px] text-gray-500 uppercase font-bold mt-1">{label}</p>
              </div>
            ))}
          </div>

          {/* Filtres et recherche */}
          <div className="flex flex-col sm:flex-row gap-3 justify-between items-stretch sm:items-center">
            <div className="flex flex-wrap gap-2">
              {[
                { value: '', label: t('Toutes', 'الكل') },
                { value: 'pending', label: t('En attente', 'قيد الانتظار') },
                { value: 'paid', label: t('Payées', 'مدفوعة') },
                { value: 'expired', label: t('Expirées', 'منتهية') },
              ].map(({ value, label }) => (
                <button
                  key={value || 'all'}
                  onClick={() => setReservationFilter(value)}
                  className={`px-3 py-1.5 rounded-lg text-[10px] font-bold transition-all ${
                    reservationFilter === value
                      ? 'bg-purple-600 text-white'
                      : 'bg-[#12141c] text-gray-400 border border-gray-900 hover:text-white'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <div className="relative flex-1 sm:w-56">
                <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                <input
                  type="text"
                  value={reservationSearch}
                  onChange={(e) => setReservationSearch(e.target.value)}
                  placeholder={t('Nom ou email...', 'اسم أو بريد...')}
                  className="w-full pl-9 pr-3 py-2 bg-[#12141c] border border-gray-900 rounded-xl text-xs text-white placeholder-gray-600 outline-none focus:border-purple-600/50"
                />
              </div>
              <button
                onClick={refreshReservations}
                className="px-3 py-2 bg-[#12141c] border border-gray-900 rounded-xl text-gray-400 hover:text-white transition-all"
                title={t('Actualiser', 'تحديث')}
              >
                <RefreshCw size={14} />
              </button>
            </div>
          </div>

          {/* Tableau des réservations */}
          <div className="bg-[#12141c] border border-gray-900 rounded-2xl overflow-hidden shadow-xl">
            {reservations.length === 0 ? (
              <div className="text-center py-16 text-gray-600 text-xs space-y-2 flex flex-col items-center">
                <AppIcon name="clipboardEmpty" size={48} alt="" />
                <p>{t('Aucune réservation trouvée.', 'لا توجد حجوزات.')}</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-gray-900 text-gray-500 font-bold text-[10px] tracking-wider uppercase bg-[#161922]/50">
                      <th className="p-4">{t('Nom réservé', 'الاسم المحجوز')}</th>
                      <th className="p-4">{t('Client', 'العميل')}</th>
                      <th className="p-4">{t('Forfait', 'الباقة')}</th>
                      <th className="p-4">{t('Statut', 'الحالة')}</th>
                      <th className="p-4">{t('Créée le', 'تاريخ الإنشاء')}</th>
                      <th className="p-4 text-center w-40">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-900/60 text-xs font-medium">
                    {reservations.map((r) => (
                      <tr key={r.id} className="hover:bg-[#161922]/30 transition-all">
                        <td className="p-4">
                          <span className="font-bold text-white tracking-wide">{r.nom}</span>
                          <span className="block text-[10px] text-gray-600 uppercase mt-0.5">{r.langue}</span>
                        </td>
                        <td className="p-4 text-gray-400">
                          {r.client_prenom || r.client_nom ? (
                            <>
                              <span className="block text-white font-medium">{r.client_prenom} {r.client_nom}</span>
                              <span className="block text-[10px]">{r.client_email || r.user_email}</span>
                              {r.card_last4 && (
                                <span className="block text-[10px] text-gray-600 mt-0.5">
                                  **** {r.card_last4} · {r.card_expiry || '—'}
                                </span>
                              )}
                            </>
                          ) : (
                            r.user_email
                          )}
                        </td>
                        <td className="p-4">
                          <span className="bg-purple-950/40 text-purple-300 border border-purple-900/30 px-2 py-0.5 rounded-md text-[10px] uppercase font-bold">
                            {r.forfait || 'free'}
                          </span>
                        </td>
                        <td className="p-4">{statusBadge(r.status)}</td>
                        <td className="p-4 text-gray-500">{formatDate(r.created_at)}</td>
                        <td className="p-4">
                          <div className="flex items-center justify-center gap-1.5 flex-wrap">
                            {!r.is_paid && (
                              <button
                                onClick={() => handleReservationAction(r.id, 'mark_paid')}
                                className="w-8 h-8 rounded-lg bg-emerald-950/40 text-emerald-400 border border-emerald-900/30 flex items-center justify-center hover:bg-emerald-600 hover:text-white transition-all"
                                title={t('Marquer payée', 'تحديد كمدفوعة')}
                              >
                                <Check size={14} />
                              </button>
                            )}
                            {r.is_paid && (
                              <button
                                onClick={() => handleReservationAction(r.id, 'mark_unpaid')}
                                className="w-8 h-8 rounded-lg bg-amber-950/40 text-amber-400 border border-amber-900/30 flex items-center justify-center hover:bg-amber-600 hover:text-white transition-all"
                                title={t('Annuler paiement', 'إلغاء الدفع')}
                              >
                                <Clock size={14} />
                              </button>
                            )}
                            <button
                              onClick={() => handleReservationAction(r.id, 'extend', 30)}
                              className="w-8 h-8 rounded-lg bg-blue-950/40 text-blue-400 border border-blue-900/30 flex items-center justify-center hover:bg-blue-600 hover:text-white transition-all"
                              title={t('Prolonger 30 jours', 'تمديد 30 يوماً')}
                            >
                              <CalendarPlus size={14} />
                            </button>
                            {r.stripe_url && (
                              <a
                                href={r.stripe_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="w-8 h-8 rounded-lg bg-purple-950/40 text-purple-400 border border-purple-900/30 flex items-center justify-center hover:bg-purple-600 hover:text-white transition-all"
                                title={t('Lien Stripe', 'رابط Stripe')}
                              >
                                <ExternalLink size={14} />
                              </a>
                            )}
                            <button
                              onClick={() => handleDeleteReservation(r.id)}
                              className="w-8 h-8 rounded-lg bg-red-950/40 text-red-400 border border-red-900/30 flex items-center justify-center hover:bg-red-600 hover:text-white transition-all"
                              title={t('Supprimer', 'حذف')}
                            >
                              <Trash2 size={14} />
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
        </div>
      )}

      {/* ── ONGLET DATASETS & FINE-TUNING ── */}
      {activeTab === 'datasets' && trainingStats && (
        <div className="space-y-4">
          {/* Stats collecte SQLite */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { key: 'positive_samples', label: t('Échantillons +', 'عينات إيجابية'), color: 'text-emerald-400' },
              { key: 'negative_samples', label: t('Échantillons −', 'عينات سلبية'), color: 'text-red-400' },
              { label: t('Dataset statique', 'مجموعة ثابتة'), value: trainingStats.static_dataset_names, color: 'text-white' },
              { label: t('Prêt fine-tuning', 'جاهز للتدريب'), ready: trainingStats.ready_for_finetuning, color: trainingStats.ready_for_finetuning ? 'text-emerald-400' : 'text-amber-400' },
            ].map((item, i) => (
              <div key={i} className="bg-[#12141c] border border-gray-900 rounded-xl p-4 text-center">
                <p className={`text-2xl font-black ${item.color} flex items-center justify-center min-h-[2rem]`}>
                  {item.ready != null ? (
                    item.ready ? <AppIcon name="check" size={24} alt="" /> : '—'
                  ) : (
                    item.value ?? trainingStats[item.key] ?? 0
                  )}
                </p>
                <p className="text-[10px] text-gray-500 uppercase font-bold mt-1">{item.label}</p>
              </div>
            ))}
          </div>

          {/* Modèles LLM locaux */}
          <div className="bg-[#12141c] border border-gray-900 rounded-2xl p-5 space-y-3">
            <h3 className="text-sm font-bold text-purple-400 flex items-center gap-2">
              <Brain size={16} />
              {t('Modèles LLM open source (Mode B local)', 'نماذج LLM مفتوحة المصدر')}
            </h3>
            <div className="grid sm:grid-cols-3 gap-3">
              {localModels.map((m) => (
                <div key={m.key} className="bg-[#0b0c10] border border-gray-900 rounded-xl p-3 text-xs">
                  <p className="font-bold text-white">{m.label}</p>
                  <p className="text-gray-500 mt-1">{m.langues?.join(', ')}</p>
                  <code className="block mt-2 text-[10px] text-purple-400 bg-purple-950/30 px-2 py-1 rounded">
                    {m.pull_cmd}
                  </code>
                </div>
              ))}
            </div>
            <p className="text-[10px] text-gray-600">
              {t(
                'Ces modèles utilisent automatiquement vos datasets + likes/favoris/réservations pour enrichir les prompts.',
                'تستخدم هذه النماذج تلقائياً مجموعات البيانات + الإعجابات/المفضلة/الحجوزات لإثراء المطالبات.'
              )}
            </p>
          </div>

          {/* Actions export & sync */}
          <div className="bg-[#12141c] border border-gray-900 rounded-2xl p-5 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Download size={16} className="text-emerald-400" />
                {t('Export fine-tuning', 'تصدير للتدريب الدقيق')}
              </h3>
              <button
                type="button"
                onClick={() => setFinetuningGuideOpen(true)}
                className="px-3 py-2 bg-purple-950/40 hover:bg-purple-900/50 border border-purple-800/40 text-purple-300 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all"
              >
                <BookOpen size={14} />
                {t('Guide fine-tuning', 'دليل التدريب الدقيق')}
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              <button onClick={() => handleExportTraining('jsonl')} className="px-3 py-2 bg-purple-600 hover:bg-purple-500 rounded-xl text-xs font-bold">
                JSONL {t('(Llama/Qwen)', '')}
              </button>
              <button onClick={() => handleExportTraining('jsonl', 'fr')} className="px-3 py-2 bg-[#1f2833] border border-gray-800 hover:border-purple-600/50 rounded-xl text-xs font-bold">
                JSONL FR
              </button>
              <button onClick={() => handleExportTraining('jsonl', 'ar')} className="px-3 py-2 bg-[#1f2833] border border-gray-800 hover:border-purple-600/50 rounded-xl text-xs font-bold">
                JSONL AR
              </button>
              <button onClick={() => handleExportTraining('alpaca')} className="px-3 py-2 bg-[#1f2833] border border-gray-800 hover:border-purple-600/50 rounded-xl text-xs font-bold">
                Alpaca
              </button>
              <button onClick={() => handleExportTraining('csv')} className="px-3 py-2 bg-[#1f2833] border border-gray-800 hover:border-purple-600/50 rounded-xl text-xs font-bold">
                CSV
              </button>
              <button onClick={handleSyncDatasets} className="px-3 py-2 bg-emerald-700 hover:bg-emerald-600 rounded-xl text-xs font-bold flex items-center gap-1.5">
                <RefreshCw size={12} />
                {t('Sync → data/', 'مزامنة → data/')}
              </button>
            </div>
            <p className="text-[10px] text-gray-600">
              {t(
                `Minimum recommandé : ${trainingStats.recommended_min_samples} échantillons positifs. Sources : likes, favoris, réservations payées.`,
                `الحد الأدنى الموصى به: ${trainingStats.recommended_min_samples} عينة. المصادر: الإعجابات، المفضلة، الحجوزات المدفوعة.`
              )}
            </p>
          </div>
        </div>
      )}

      {/* MODALE GUIDE FINE-TUNING */}
      {finetuningGuideOpen && trainingStats && (
        <div
          className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4 animate-fade-in"
          dir={lang === 'ar' ? 'rtl' : 'ltr'}
          onClick={() => setFinetuningGuideOpen(false)}
        >
          <div
            className="bg-[#12141c] border border-purple-900/30 rounded-3xl p-6 max-w-lg w-full text-white shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center border-b border-gray-900 pb-3">
              <h3 className="text-sm font-bold text-purple-400 flex items-center gap-2">
                <BookOpen size={16} />
                {t('Guide fine-tuning', 'دليل التدريب الدقيق')}
              </h3>
              <button
                type="button"
                onClick={() => setFinetuningGuideOpen(false)}
                className="text-gray-500 hover:text-white font-bold text-lg bg-[#1f2833]/40 w-8 h-8 rounded-full flex items-center justify-center"
              >
                ×
              </button>
            </div>

            <div className={`rounded-xl p-3 text-xs border ${
              trainingStats.ready_for_finetuning
                ? 'bg-emerald-950/30 border-emerald-900/40 text-emerald-300'
                : 'bg-amber-950/30 border-amber-900/40 text-amber-300'
            }`}>
              {trainingStats.ready_for_finetuning ? (
                t(
                  `Prêt : ${trainingStats.positive_samples} échantillons positifs (seuil ${trainingStats.recommended_min_samples} atteint).`,
                  `جاهز: ${trainingStats.positive_samples} عينة إيجابية (تم بلوغ الحد ${trainingStats.recommended_min_samples}).`
                )
              ) : (
                t(
                  `En cours : ${trainingStats.positive_samples}/${trainingStats.recommended_min_samples} échantillons positifs. Encouragez les likes, favoris et réservations payées.`,
                  `قيد التقدم: ${trainingStats.positive_samples}/${trainingStats.recommended_min_samples} عينة. شجّع الإعجابات والمفضلة والحجوزات المدفوعة.`
                )
              )}
            </div>

            <p className="text-[11px] text-gray-500 leading-relaxed">
              {t(
                'Les échantillons + proviennent des likes, favoris et réservations payées. Les − proviennent des dislikes. L\'app n\'entraîne pas le modèle automatiquement : vous exportez les données puis fine-tunez en local.',
                'العينات + من الإعجابات والمفضلة والحجوزات المدفوعة. العينات − من عدم الإعجاب. التطبيق لا يدرّب النموذج تلقائياً: تصدّر البيانات ثم تدرّب محلياً.'
              )}
            </p>

            <ol className="space-y-3 text-xs">
              {[
                {
                  title: t('Sync → data/ (effet immédiat)', 'مزامنة → data/ (فوري)'),
                  body: t(
                    'Cliquez « Sync → data/ » pour copier les noms validés dans le dossier data/. Améliore tout de suite le Mode A (nanoGPT) et le few-shot du Mode B, sans réentraînement.',
                    'انقر « مزامنة → data/ » لنسخ الأسماء المعتمدة إلى مجلد data/. يحسّن فوراً الوضع A و few-shot للوضع B دون إعادة تدريب.'
                  ),
                  action: handleSyncDatasets,
                  actionLabel: t('Lancer la sync', 'بدء المزامنة'),
                },
                {
                  title: t('Exporter le dataset JSONL', 'تصدير JSONL'),
                  body: t(
                    'Téléchargez « JSONL (Llama/Qwen) » (ou JSONL FR / AR). Format compatible Llama 3.1 et Qwen 2.5 pour le fine-tuning.',
                    'حمّل « JSONL (Llama/Qwen) » (أو FR / AR). متوافق مع Llama 3.1 و Qwen 2.5.'
                  ),
                  action: () => handleExportTraining('jsonl'),
                  actionLabel: t('Exporter JSONL', 'تصدير JSONL'),
                },
                {
                  title: t('Installer Ollama + modèle', 'تثبيت Ollama + النموذج'),
                  body: t(
                    'Sur votre machine : installez Ollama (ollama.com), puis par ex. ollama pull llama3.1 ou ollama pull qwen2.5.',
                    'على جهازك: ثبّت Ollama (ollama.com)، ثم مثلاً ollama pull llama3.1 أو ollama pull qwen2.5.'
                  ),
                },
                {
                  title: t('Fine-tuner en local (hors app)', 'التدريب الدقيق محلياً'),
                  body: t(
                    'Utilisez le fichier .jsonl avec LLaMA-Factory, Unsloth ou la doc Ollama fine-tuning. Entraînez sur vos likes/favoris/réservations.',
                    'استخدم ملف .jsonl مع LLaMA-Factory أو Unsloth أو وثائق Ollama. درّب على الإعجابات/المفضلة/الحجوزات.'
                  ),
                },
                {
                  title: t('Utiliser en Mode B', 'الاستخدام في الوضع B'),
                  body: t(
                    'Dans l\'app, choisissez Mode B et un modèle local : ollama-llama31, ollama-qwen25 ou ollama-mistral. Les prompts restent enrichis par SQLite + data/.',
                    'في التطبيق، اختر الوضع B ونموذجاً محلياً: ollama-llama31 أو ollama-qwen25 أو ollama-mistral.'
                  ),
                },
              ].map((step, i) => (
                <li key={i} className="flex gap-3 bg-[#0b0c10] border border-gray-900 rounded-xl p-3">
                  <span className="shrink-0 w-6 h-6 rounded-full bg-purple-600 text-white text-[10px] font-black flex items-center justify-center">
                    {i + 1}
                  </span>
                  <div className="space-y-1.5 min-w-0">
                    <p className="font-bold text-white">{step.title}</p>
                    <p className="text-gray-500 leading-relaxed">{step.body}</p>
                    {step.action && (
                      <button
                        type="button"
                        onClick={() => { step.action(); setFinetuningGuideOpen(false); }}
                        className="mt-1 px-2.5 py-1 bg-purple-600/80 hover:bg-purple-600 rounded-lg text-[10px] font-bold"
                      >
                        {step.actionLabel}
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ol>

            <p className="text-[10px] text-gray-600 border-t border-gray-900 pt-3">
              {t(
                'Note : le Mode B enrichit déjà les prompts avec likes/favoris en direct. Sync et export accélèrent et pérennisent cette amélioration.',
                'ملاحظة: الوضع B يُثرِي المطالبات تلقائياً. المزامنة والتصدير يثبتان هذا التحسين.'
              )}
            </p>
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
