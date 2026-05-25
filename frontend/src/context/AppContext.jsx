import React, { createContext, useState, useContext, useEffect } from 'react';

const AppContext = createContext();

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
    // ⚡ AJOUT DES CLÉS EN MINUSCULES POUR LE SÉCURISER AVEC .toLowerCase()
    "tous": "Tous",
    "futuriste": "Futuriste",
    "luxe": "Luxe",
    "tech": "Tech",
    "minimal": "Minimal",
    "corporate": "Entreprise",
    // Conservation des anciennes clés au cas où
    "Tous": "Tous",
    "Futuriste": "Futuriste",
    "Luxe": "Luxe",
    "Tech": "Tech",
    "Minimal": "Minimal",
    // Nouvelles catégories
    "general": "Tout",
    "food": "Food",
    "services": "Services",
    "industrie": "Industrie"
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
    // ⚡ AJOUT DES CLÉS EN MINUSCULES TRADUITES EN ARABE
    "tous": "الكل",
    "futuriste": "مستقبلي",
    "luxe": "فاخر",
    "tech": "تقني",
    "minimal": "بسيط",
    "corporate": "مؤسسي",
    // Conservation des anciennes clés au cas où
    "Tous": "الكل",
    "Futuriste": "مستقبلي",
    "Luxe": "فاخر",
    "Tech": "تقني",
    "Minimal": "بسيط",
    // Nouvelles catégories
    "general": "الكل",
    "food": "غذاء",
    "services": "خدمات",
    "industrie": "صناعة"
  }
};

export const AppProvider = ({ children }) => {
  const [lang, setLang] = useState('fr');
  const [favorites, setFavorites] = useState([]);
  const [categories, setCategories] = useState(null);

  // Load categories config
  useEffect(() => {
    const loadCategories = async () => {
      try {
        const res = await fetch('/categories.json');
        const data = await res.json();
        setCategories(data);
      } catch (error) {
        console.error('Failed to load categories:', error);
      }
    };
    loadCategories();
  }, []);

  // Inversion automatique du sens de lecture de la page (RTL / LTR)
  useEffect(() => {
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.lang = lang;
  }, [lang]);

  const t = (key) => translations[lang][key] || key;

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
      favorites,
      addFavorite,
      removeFavorite,
      exportToCSV,
      exportToJSON,
      categories
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);