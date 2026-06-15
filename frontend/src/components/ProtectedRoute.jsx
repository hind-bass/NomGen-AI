// src/components/ProtectedRoute.jsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';

export default function ProtectedRoute({ children, requiredRole }) {
  const { token, userRole } = useApp();

  // Si l'utilisateur n'est pas connecté, redirection vers la page de login
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Si un rôle spécifique est demandé (ex: 'admin') et que l'utilisateur ne l'a pas
  if (requiredRole && userRole !== requiredRole) {
    return <Navigate to="/" replace />; // Redirection vers l'accueil standard
  }

  return children;
}