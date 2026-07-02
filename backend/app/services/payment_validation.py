import re
from datetime import datetime


def validate_card_format(card_number: str) -> bool:
    """
    Valide le format d'un numéro de carte bancaire.
    Accepte 13 à 19 chiffres (Visa, Mastercard, Amex, etc.) sans exiger Luhn.
    """
    digits = normalize_card_digits(card_number)
    return bool(re.match(r"^\d{13,19}$", digits))


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def validate_card_expiry(expiry: str) -> bool:
    """Valide le format MM/YY ou MM/YYYY et vérifie que la carte n'est pas expirée."""
    expiry = expiry.strip()
    match = re.match(r"^(0[1-9]|1[0-2])\s*/\s*(\d{2}|\d{4})$", expiry)
    if not match:
        return False
    month = int(match.group(1))
    year_raw = match.group(2)
    year = int(year_raw) if len(year_raw) == 4 else 2000 + int(year_raw)
    now = datetime.utcnow()
    if year < now.year or (year == now.year and month < now.month):
        return False
    return True


def validate_cvc(cvc: str) -> bool:
    return bool(re.match(r"^\d{3,4}$", cvc.strip()))


def normalize_card_digits(card: str) -> str:
    return re.sub(r"\D", "", card)


def card_last4(card: str) -> str:
    digits = normalize_card_digits(card)
    return digits[-4:] if len(digits) >= 4 else digits


def validate_payment_form(
    *,
    forfait: str,
    client_nom: str,
    client_prenom: str,
    client_email: str,
    numero_carte: str = "",
    card_expiry: str = "",
    card_cvc: str = "",
) -> tuple[bool, str]:
    """
    Valide le formulaire de réservation.
    Retourne (True, "") ou (False, message_d_erreur).
    """
    if forfait not in ("free", "pro", "max"):
        return False, "Forfait invalide."

    if len(client_prenom.strip()) < 2:
        return False, "Le prénom doit contenir au moins 2 caractères."
    if len(client_nom.strip()) < 2:
        return False, "Le nom doit contenir au moins 2 caractères."
    if not validate_email(client_email):
        return False, "Adresse e-mail invalide."

    if forfait == "free":
        return True, ""

    digits = normalize_card_digits(numero_carte)
    if not validate_card_format(digits):
        return False, "Numéro de carte invalide (13 à 19 chiffres requis)."
    if not validate_card_expiry(card_expiry):
        return False, "Date d'expiration invalide ou carte expirée (format MM/AA)."
    if not validate_cvc(card_cvc):
        return False, "CVC invalide (3 ou 4 chiffres)."

    return True, ""
