# Backend Admin API Documentation

## Nouvelle Fonctionnalité : Gestion Administrateur

### Routes Admin Disponibles

#### 1. Gestion des Utilisateurs

**Créer un utilisateur** (POST)
```
POST /api/admin/users
Authorization: Bearer {admin_token}

{
  "email": "user@example.com",
  "password": "password123",
  "role": "user",           # "user" ou "admin"
  "is_active": true
}
```

**Lister tous les utilisateurs** (GET)
```
GET /api/admin/users
Authorization: Bearer {admin_token}
```

Réponse:
```json
[
  {
    "id": 1,
    "email": "admin@example.com",
    "role": "admin",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00"
  },
  ...
]
```

**Modifier un utilisateur** (PATCH)
```
PATCH /api/admin/users/{user_id}
Authorization: Bearer {admin_token}

{
  "role": "admin",          # Optionnel
  "is_active": false        # Optionnel
}
```

**Supprimer un utilisateur** (DELETE)
```
DELETE /api/admin/users/{user_id}
Authorization: Bearer {admin_token}
```

#### 2. Gestion des Suggestions

**Lister toutes les suggestions** (GET)
```
GET /api/admin/suggestions?status_filter=pending
Authorization: Bearer {admin_token}

# Parameters:
# - status_filter: "pending", "approved", "rejected" (optionnel)
```

Réponse:
```json
[
  {
    "id": 1,
    "nom": "brandname",
    "langue": "fr",
    "secteur": "LUXE",
    "type_nom": "marque",
    "status": "pending",
    "user_id": 2,
    "submitted_at": "2024-01-15T10:30:00",
    "reviewed_at": null
  },
  ...
]
```

**Ajouter une suggestion directement** (POST)
```
POST /api/admin/suggestions/add
Authorization: Bearer {admin_token}

{
  "nom": "brandname",
  "langue": "fr",
  "secteur": "LUXE",
  "type_nom": "marque"
}
```

Comportement:
- ✓ Vérifie si le nom existe dans le fichier dataset
- ✓ Vérifie si le nom existe en base (approved ou pending)
- ✓ Si validation OK: ajoute au fichier .txt ET en base avec statut "approved"
- ✗ Retourne 409 CONFLICT si le nom existe déjà

Réponse (201 Created):
```json
{
  "message": "'brandname' ajouté avec succès.",
  "fichier": "fr/marque/luxe.txt",
  "suggestion_id": 3
}
```

**Valider/Rejeter une suggestion** (PATCH)
```
PATCH /api/admin/suggestions/{suggestion_id}
Authorization: Bearer {admin_token}

{
  "action": "approve"     # "approve" ou "reject"
}
```

Comportement:
- Si "approve": ajoute le nom au dataset .txt et passe le statut à "approved"
- Si "reject": passe le statut à "rejected" (rien ajouté au dataset)
- Retourne 400 si la suggestion a déjà été traitée
- Retourne 409 CONFLICT si le nom existe déjà dans le dataset

Réponse:
```json
{
  "message": "Suggestion approved.",
  "suggestion_id": 1,
  "status": "approved"
}
```

### Vérification des Doublons

Le système vérifie les doublons à **3 niveaux**:

1. **Fichier Dataset** (`/data/{langue}/{type}/{secteur}.txt`)
   - Vérification case-insensitive
   - Trim des espaces
   
2. **Base de Données - Approved**
   - Les suggestions approuvées ne peuvent pas être ajoutées en doublon
   
3. **Base de Données - Pending**
   - Les suggestions en attente ne peuvent pas être soumises en doublon

### Flux de Modération

```
USER SUBMISSION
    ↓
POST /api/suggestions (user)
    ↓
Saved as "pending" in DB
    ↓
ADMIN REVIEW
    ↓
PATCH /api/admin/suggestions/{id} (admin)
    ↓
    ├─→ action: "approve"
    │   ├─ Ajoute au fichier .txt
    │   └─ Status → "approved"
    │
    └─→ action: "reject"
        └─ Status → "rejected"

OU

DIRECT ADD (Admin Only)
    ↓
POST /api/admin/suggestions/add (admin)
    ├─ Vérifie doublons
    ├─ Ajoute directement au fichier .txt
    └─ Enregistre comme "approved" en DB
```

### Codes HTTP

- **201 Created**: Succès création
- **204 No Content**: Succès suppression
- **400 Bad Request**: Données invalides (ex: suggestion déjà traitée)
- **401 Unauthorized**: Token absent ou invalide
- **403 Forbidden**: Accès admin requis
- **404 Not Found**: Ressource introuvable
- **409 Conflict**: Doublon détecté

### Authentification

Toutes les routes admin nécessitent un token JWT avec rôle "admin":

```
Authorization: Bearer {jwt_token}
```

Pour obtenir un token admin:
1. Créer un compte via `POST /auth/register`
2. Admin: modifier le rôle via `PATCH /api/admin/users/{id}` avec `{"role": "admin"}`
3. Se connecter via `POST /auth/login`
4. Utiliser le token retourné

### Exemple Complet: Ajouter une Suggestion et l'Approuver

```bash
# 1. User soumet une suggestion
curl -X POST http://localhost:8000/api/suggestions \
  -H "Authorization: Bearer {user_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Luxora",
    "langue": "fr",
    "categorie": "LUXE",
    "type_nom": "marque"
  }'

# Réponse: {"id": 5, "nom": "Luxora", "status": "pending", ...}

# 2. Admin approuve la suggestion
curl -X PATCH http://localhost:8000/api/admin/suggestions/5 \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{"action": "approve"}'

# Réponse: {"message": "Suggestion approved.", "status": "approved"}

# Le nom est maintenant ajouté au fichier data/fr/marque/luxe.txt
```

### Fichiers de Données

Structure:
```
data/
├── fr/
│   ├── marque/
│   │   ├── general.txt
│   │   ├── luxe.txt
│   │   ├── tech.txt
│   │   └── ...
│   └── societe/
│       └── ...
├── ar/
│   ├── marque/
│   └── societe/
└── en/
    └── ...
```

Chaque fichier contient une liste de noms, un par ligne (lowercase).
