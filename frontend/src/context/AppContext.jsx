import React, { createContext, useState, useContext, useEffect } from 'react';

const AppContext = createContext();

// Fonction utilitaire interne pour décoder le JWT et lire le rôle sans dépendance externe
const parseJwt = (token) => {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch (e) {
    return null;
  }
};

// Dictionnaire de traduction pour basculer toute l'interface
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
  const [lang, setLang] = useState('fr');
  const [favorites, setFavorites] = useState([]);
  
  // ⚡ ÉTATS D'AUTHENTIFICATION AVANCÉS & PERSISTANTS
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [user, setUser] = useState(null); 
  const [userRole, setUserRole] = useState('user'); // 'user' ou 'admin'

  // Écouteur de Token pour synchroniser le rôle, l'utilisateur et le localStorage
  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      const decoded = parseJwt(token);
      if (decoded) {
        setUserRole(decoded.role || 'user');
        // Si l'état user est vide mais qu'on a un token valide, on reconstruit le profil minimal
        if (!user) {
          setUser({ email: decoded.sub, id: decoded.user_id });
        }
      }
    } else {
      // ⚡ CORRECTION : Si le token devient null, on nettoie TOUT immédiatement de manière stricte
      localStorage.removeItem('token');
      setUser(null);
      setUserRole('user');
    }
  }, [token]);

  // Inversion automatique du sens de lecture de la page (RTL / LTR)
  useEffect(() => {
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.lang = lang;
  }, [lang]);

  const t = (key) => translations[lang][key] || key;

  // ⚡ Fonctions d'authentification globales adaptées au JWT
  const loginUser = (userData, receivedToken) => {
    setUser(userData);
    if (receivedToken) {
      setToken(receivedToken);
    }
  };

  // ⚡ CORRECTION SÉCURISÉE DE LA DÉCONNEXION (Évite l'effet figé/statique)
  const logoutUser = () => {
    localStorage.removeItem('token'); // Nettoyage physique instantané du stockage local
    setUser(null);                    // Réinitialisation immédiate du profil de l'utilisateur
    setUserRole('user');              // Remise à zéro instantanée du rôle par défaut
    setToken(null);                   // Alerte instantanée de l'application pour re-render l'AuthScreen
  };

  // Fonction pour ajouter un favori s'il n'existe pas déjà
  const addFavorite = (nameObj) => {
    if (nameObj && !favorites.some(fav => fav.nom === nameObj.nom)) {
      setFavorites([...favorites, nameObj]);
    }
  };

  // Fonction pour supprimer un favori
  const removeFavorite = (name) => {
    setFavorites(favorites.filter(fav => fav.nom !== name));
  };

  // EXPORT CSV
  const exportToCSV = () => {
    if (favorites.length === 0) return;
    const csvContent = "data:text/csv;charset=utf-8," 
      + ["Nom,Secteur,Langue,Score"].join(",") + "\n"
      + favorites.map(f => `"${f.nom}","${f.secteur || ''}","${f.langue || ''}",${f.score || ''}`).join("\n");
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "brandforge_favorites.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // EXPORT JSON
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
      token,        // Export du jeton JWT brut
      user,         // Export de l'état utilisateur (email, id)
      userRole,     // Export du rôle explicite ('admin' ou 'user')
      loginUser,    // Fonction de connexion
      logoutUser,   // Fonction de déconnexion
      favorites, 
      addFavorite, 
      removeFavorite, 
      exportToCSV, 
      exportToJSON
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);
