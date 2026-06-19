import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { API_BASE } from '../config/api';

const AppContext = createContext();

const parseJwt = (token) => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    if (payload.exp && payload.exp * 1000 < Date.now()) {
      return null;
    }
    return payload;
  } catch (e) {
    return null;
  }
};

const getInitialAuth = () => {
  const stored = localStorage.getItem('token');
  if (!stored) {
    return { token: null, user: null, userRole: 'user' };
  }
  const decoded = parseJwt(stored);
  if (!decoded) {
    localStorage.removeItem('token');
    return { token: null, user: null, userRole: 'user' };
  }
  return {
    token: stored,
    user: { email: decoded.sub, id: decoded.user_id, role: decoded.role },
    userRole: decoded.role || 'user',
  };
};

const translations = {
  fr: {
    title: "Nommez votre vision",
    subtitle: "Générez des noms de marque percutants grâce à l'IA",
    btnCompany: "Noms d'entreprise",
    descCompany: "Startups, agences, sociétés",
    btnBrand: "Noms de marque",
    descBrand: "Produits, collections, identités",
    placeholder: "Décrivez votre concept... ex: startup tech moderne, luxe durable",
    styleTitle: "STYLE :",
    btnGenerate: "Générer",
    swipeLeft: "Glisser à gauche pour passer",
    swipeRight: "Glisser à droite pour aimer",
    favTitle: "Mes Favoris",
    noFav: "Aucun favori pour le moment",
    remaining: "restants",
    styleAll: "Tous",
    styleFuturistic: "Futuriste",
    styleLuxe: "Luxe",
    styleTech: "Tech",
    styleMinimal: "Minimal",
    "tous": "Tous",
    "futuriste": "Futuriste",
    "luxe": "Luxe",
    "tech": "Tech",
    "minimal": "Minimal",
    "corporate": "Entreprise",
    "Tous": "Tous",
    "Futuriste": "Futuriste",
    "Luxe": "Luxe",
    "Tech": "Tech",
    "Minimal": "Minimal"
  },
  ar: {
    title: "سمِّ رؤيتك",
    subtitle: "أشئ أسماء علامات تجارية مميزة ومؤثرة بفضل الذكاء الاصطناعي",
    btnCompany: "أسماء شركات",
    descCompany: "شركات ناشئة، وكالات، مؤسسات",
    btnBrand: "أسماء علامات تجارية",
    descBrand: "منتجات، مجموعات، هويات",
    placeholder: "صف فكرتك... مثال: شركة تقنية حديثة، مشروع فاخر مستدام",
    styleTitle: "الأسلوب :",
    btnGenerate: "توليد الأسماء",
    swipeLeft: "اسحب لليسار للتخطي",
    swipeRight: "اسحب لليمين للإعجاب",
    favTitle: "قائمـة المفضلة",
    noFav: "لا توجد أي مفضلة حالياً",
    remaining: "متبقية",
    styleAll: "الكل",
    styleFuturistic: "مستقبلي",
    styleLuxe: "فاخر",
    styleTech: "تقني",
    styleMinimal: "بسيط",
    "tous": "الكل",
    "futuriste": "مستقبلي",
    "luxe": "فاخر",
    "tech": "تقني",
    "minimal": "بسيط",
    "corporate": "مؤسسي",
    "Tous": "الكل",
    "Futuriste": "مستقبلي",
    "Luxe": "فاخر",
    "Tech": "تقني",
    "Minimal": "بسيط"
  }
};

export const AppProvider = ({ children }) => {
  const initialAuth = getInitialAuth();
  const [lang, setLang] = useState('fr');
  const [favorites, setFavorites] = useState([]);
  const [token, setToken] = useState(initialAuth.token);
  const [user, setUser] = useState(initialAuth.user);
  const [userRole, setUserRole] = useState(initialAuth.userRole);

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      const decoded = parseJwt(token);
      if (decoded) {
        setUserRole(decoded.role || 'user');
        if (!user) {
          setUser({ email: decoded.sub, id: decoded.user_id });
        }
      }
    } else {
      localStorage.removeItem('token');
      setUser(null);
      setUserRole('user');
      setFavorites([]);
    }
  }, [token]);

  // Charger les favoris persistants depuis SQLite au login / refresh
  useEffect(() => {
    if (!token) return;

    async function loadFavorites() {
      try {
        const response = await fetch(`${API_BASE}/api/favorites/`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (response.ok) {
          const data = await response.json();
          setFavorites(
            data.map((f) => ({
              id: f.id,
              nom: f.nom,
              score: f.score,
              langue: f.langue,
              secteur: f.secteur,
            }))
          );
        }
      } catch (e) {
        console.error('Erreur chargement favoris:', e);
      }
    }
    loadFavorites();
  }, [token]);

  useEffect(() => {
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.lang = lang;
  }, [lang]);

  const t = (key) => translations[lang][key] || key;

  const loginUser = (userData, receivedToken) => {
    if (!receivedToken) return;
    const decoded = parseJwt(receivedToken);
    if (!decoded) return;
    localStorage.setItem('token', receivedToken);
    setToken(receivedToken);
    setUserRole(decoded.role || 'user');
    setUser({
      email: decoded.sub || userData?.email,
      id: decoded.user_id,
      role: decoded.role || 'user',
    });
  };

  const logoutUser = () => {
    localStorage.removeItem('token');
    setUser(null);
    setUserRole('user');
    setToken(null);
    setFavorites([]);
  };

  const addFavorite = useCallback(async (nameObj) => {
    if (!nameObj?.nom) return;
    if (favorites.some((f) => f.nom === nameObj.nom)) return;

    const payload = {
      nom: nameObj.nom,
      score: nameObj.score || 0,
      langue: nameObj.langue || 'fr',
      secteur: nameObj.secteur || nameObj.style || 'GENERAL',
    };

    if (token) {
      try {
        const response = await fetch(`${API_BASE}/api/favorites/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        });
        if (response.ok) {
          const saved = await response.json();
          setFavorites((prev) => [
            ...prev,
            {
              id: saved.id,
              nom: saved.nom,
              score: saved.score,
              langue: saved.langue,
              secteur: saved.secteur,
              generation_id: nameObj.generation_id,
            },
          ]);
          // Alimente aussi la table favoris (fine-tuning)
          if (nameObj.generation_id) {
            fetch(`${API_BASE}/favorites/add`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify({ generation_id: nameObj.generation_id }),
            }).catch(() => {});
          }
          return;
        }
        if (response.status === 409) return; // déjà en favoris
      } catch (e) {
        console.error('Erreur sauvegarde favori:', e);
      }
    }

    setFavorites((prev) => [...prev, { ...nameObj, ...payload }]);
  }, [favorites, token]);

  const removeFavorite = useCallback(async (idOrNom) => {
    const fav = favorites.find((f) => f.id === idOrNom || f.nom === idOrNom);
    if (!fav) return;

    if (token && fav.id) {
      try {
        await fetch(`${API_BASE}/api/favorites/${fav.id}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch (e) {
        console.error('Erreur suppression favori:', e);
      }
    }
    setFavorites((prev) => prev.filter((f) => f.nom !== fav.nom));
  }, [favorites, token]);

  const exportToCSV = () => {
    if (favorites.length === 0) return;
    const csvContent = "data:text/csv;charset=utf-8,"
      + ["Nom,Secteur,Langue,Score"].join(",") + "\n"
      + favorites.map((f) => `"${f.nom}","${f.secteur || ''}","${f.langue || ''}",${f.score || ''}`).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "brandforge_favorites.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportToJSON = () => {
    if (favorites.length === 0) return;
    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(
      JSON.stringify(favorites, null, 2)
    )}`;
    const link = document.createElement("a");
    link.setAttribute("href", jsonString);
    link.setAttribute("download", "brandforge_favorites.json");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <AppContext.Provider value={{
      lang,
      setLang,
      t,
      token,
      user,
      userRole,
      loginUser,
      logoutUser,
      favorites,
      addFavorite,
      removeFavorite,
      exportToCSV,
      exportToJSON,
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);
