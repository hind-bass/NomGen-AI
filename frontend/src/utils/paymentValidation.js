/**
 * Validation côté client du formulaire de paiement (miroir du backend).
 */

export function validateCardFormat(cardNumber) {
  const digits = cardNumber.replace(/\D/g, '');
  return /^\d{13,19}$/.test(digits);
}

export function validateEmail(email) {
  return /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(email.trim());
}

export function validateExpiry(expiry) {
  const match = expiry.trim().match(/^(0[1-9]|1[0-2])\s*\/\s*(\d{2}|\d{4})$/);
  if (!match) return false;
  const month = parseInt(match[1], 10);
  const yearRaw = match[2];
  const year = yearRaw.length === 4 ? parseInt(yearRaw, 10) : 2000 + parseInt(yearRaw, 10);
  const now = new Date();
  const expEnd = new Date(year, month, 0);
  return expEnd >= new Date(now.getFullYear(), now.getMonth(), 1);
}

export function formatCardNumber(value) {
  const digits = value.replace(/\D/g, '').slice(0, 19);
  return digits.replace(/(\d{4})(?=\d)/g, '$1 ').trim();
}

export function formatExpiry(value) {
  const digits = value.replace(/\D/g, '').slice(0, 4);
  if (digits.length <= 2) return digits;
  return `${digits.slice(0, 2)}/${digits.slice(2)}`;
}

export function validateBillingForm(data, plan, lang = 'fr') {
  const t = (fr, ar) => (lang === 'ar' ? ar : fr);

  if (!data.prenom?.trim() || data.prenom.trim().length < 2) {
    return t('Le prénom doit contenir au moins 2 caractères.', 'يجب أن يحتوي الاسم الشخصي على حرفين على الأقل.');
  }
  if (!data.nom?.trim() || data.nom.trim().length < 2) {
    return t('Le nom doit contenir au moins 2 caractères.', 'يجب أن يحتوي اسم العائلة على حرفين على الأقل.');
  }
  if (!validateEmail(data.email || '')) {
    return t('Adresse e-mail invalide.', 'البريد الإلكتروني غير صالح.');
  }

  if (plan === 'free') return null;

  const digits = (data.carte || '').replace(/\D/g, '');
  if (!validateCardFormat(digits)) {
    return t('Numéro de carte invalide (13 à 19 chiffres).', 'رقم البطاقة غير صالح (13 إلى 19 رقمًا).');
  }
  if (!validateExpiry(data.expiry || '')) {
    return t('Date d\'expiration invalide ou carte expirée (MM/AA).', 'تاريخ انتهاء الصلاحية غير صالح (MM/AA).');
  }
  if (!/^\d{3,4}$/.test((data.cvc || '').trim())) {
    return t('CVC invalide (3 ou 4 chiffres).', 'رمز CVC غير صالح (3 أو 4 أرقام).');
  }

  return null;
}
