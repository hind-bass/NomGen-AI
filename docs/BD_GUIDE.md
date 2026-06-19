# 📊 Guide Complet: Base de Données SQLite

## Résumé Rapide

```
Système: SQLite (fichier embedded)
Fichier: backend/nomgen.db (44 KB)
Tables:  5 (user, suggestion, favorite, history, reservation)
```

## Zéro Configuration Requise ✨

**SQLite est déjà prêt!** Aucune installation nécessaire:

```python
# Dans backend/app/database.py:
DATABASE_URL = "sqlite:///./nomgen.db"  ← Crée automatiqu au démarrage
```

## Données Actuelles

### Utilisateurs
```
ID │ Email               │ Rôle   │ Statut    │ Créé
───┼─────────────────────┼────────┼───────────┼──────────
1  │ admin@nomgen.ai     │ admin  │ Actif     │ 15/06
2  │ admin@test.com      │ user   │ Actif     │ 16/06
3  │ user@test.com       │ user   │ Actif     │ 16/06
4  │ newuser@test.com    │ admin  │ Inactif   │ 16/06
```

### Suggestions
```
ID │ Nom        │ Langue │ Secteur  │ Status     │ User
───┼────────────┼────────┼──────────┼────────────┼─────
3  │ luxora     │ fr     │ LUXE     │ APPROVED   │ 1
4  │ ecosmart   │ fr     │ GENERAL  │ APPROVED   │ 1
5  │ luxora     │ fr     │ LUXE     │ APPROVED   │ 1
1  │ brandnex   │ fr     │ TECH     │ PENDING    │ 3
2  │ spambrand  │ fr     │ GENERAL  │ PENDING    │ 3
```

## Scripts Disponibles

### 1️⃣ Explorer les Données
```bash
python explore_db.py
```
Affiche une vue complète avec tables formatées.

### 2️⃣ Exporter en CSV
```bash
python export_db.py
```
Crée `export_user.csv`, `export_suggestion.csv`, etc.

### 3️⃣ Réinitialiser (Danger!)
```bash
python reset_db.py
```
⚠️ Supprime TOUTES les données (demande confirmation)

## API pour Gérer les Données

### Créer un Utilisateur (Admin)
```bash
curl -X POST http://localhost:8000/api/admin/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "password123",
    "role": "user"
  }'
```

### Lister les Utilisateurs
```bash
curl -X GET http://localhost:8000/api/admin/users \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Ajouter une Suggestion
```bash
curl -X POST http://localhost:8000/api/admin/suggestions/add \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Brandname",
    "langue": "fr",
    "secteur": "LUXE",
    "type_nom": "marque"
  }'
```

## Modèle de Données

### Table: user
```
id                  INTEGER PRIMARY KEY
email               TEXT UNIQUE NOT NULL
hashed_password     TEXT NOT NULL
role                TEXT ("user" | "admin")
created_at          DATETIME
is_active           BOOLEAN
```

### Table: suggestion
```
id                  INTEGER PRIMARY KEY
user_id             INTEGER FK → user.id
nom                 TEXT LOWERCASE
langue              TEXT ("fr", "ar", "en")
secteur             TEXT
type_nom            TEXT ("marque", "societe")
status              TEXT ("pending", "approved", "rejected")
submitted_at        DATETIME
reviewed_at         DATETIME
```

### Table: favorite
```
id                  INTEGER PRIMARY KEY
user_id             INTEGER FK → user.id
nom                 TEXT
score               FLOAT
langue              TEXT
secteur             TEXT
created_at          DATETIME
```

### Table: history
```
id                  INTEGER PRIMARY KEY
user_id             INTEGER FK → user.id
prompt              TEXT
langue              TEXT
secteur             TEXT
n_generated         INTEGER
mode                TEXT ("A", "B")
created_at          DATETIME
```

### Table: reservation
```
id                  INTEGER PRIMARY KEY
user_id             INTEGER FK → user.id
nom                 TEXT
langue              TEXT
secteur             TEXT
stripe_url          TEXT
expires_at          DATETIME
created_at          DATETIME
is_paid             BOOLEAN
```

## Sauvegarde et Restauration

### Sauvegarder
```bash
# Copier le fichier
cp backend/nomgen.db backend/nomgen_backup_$(date +%Y%m%d).db
```

### Restaurer
```bash
# Arrêter le serveur
# Remplacer le fichier
cp backend/nomgen_backup_20260616.db backend/nomgen.db
# Relancer le serveur
```

## Optionnel: Migrer vers PostgreSQL

### Quand?
- Si plus de 1M de suggestions
- Si plusieurs serveurs concurrents
- Si vous voulez clustering/réplication

### Changement de Code (1 ligne!)
```python
# database.py
DATABASE_URL = "postgresql://user:password@localhost/nomgen"
# Au lieu de:
DATABASE_URL = "sqlite:///./nomgen.db"
```

## Conseils

✅ **Bonnes Pratiques:**
- Sauvegarder régulièrement le fichier `.db`
- Vérifier les doublons avant d'ajouter
- Garder les données testées vs production séparées

⚠️ **Limites SQLite:**
- Max ~1 million de lignes (optimal)
- Pas de requêtes concurrent(es)
- Fichier partagé sur réseau = lent

🚀 **Scalabilité:**
```
< 100K rows     → SQLite (parfait)
100K-1M rows    → SQLite (ok)
> 1M rows       → PostgreSQL (recommandé)
```

## Accès Direct SQLite (Avancé)

### GUI: DB Browser for SQLite
Télécharger: https://sqlitebrowser.org

### CLI:
```bash
sqlite3 backend/nomgen.db
> SELECT * FROM user;
> SELECT COUNT(*) FROM suggestion;
> .tables
> .quit
```

## Logs et Debug

### Activer SQL Logging
```python
# database.py, ligne 14:
echo=True  # Voir toutes les requêtes SQL
```

### Voir les logs
```bash
tail -f backend/server.log | grep "SELECT"
```
