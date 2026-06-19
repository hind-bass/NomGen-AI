-- Exemple de données SQLite pour le système de feedback NomGen
-- Généré après : python -m app.database.init_db --seed
--
-- Tables concernées : generations, feedback, favoris

-- ── Table generations ──────────────────────────────────────────────────────
-- | id | prompt                              | langue | categorie | type_nom | nom_genere | score | mode | created_at          |
-- |----|-------------------------------------|--------|-----------|----------|------------|-------|------|---------------------|
-- | 1  | marque de luxe pour parfums         | fr     | LUXE      | marque   | Veloria    | 82.0  | B    | 2026-06-18 10:00:00 |
-- | 2  | startup tech intelligence artificielle | fr  | TECH      | societe  | NeuraLink  | 75.5  | B    | 2026-06-18 11:00:00 |
-- | 3  | restaurant bio méditerranéen        | fr     | FOOD      | marque   | Solvita    | 68.0  | A    | 2026-06-18 11:30:00 |
-- | 4  | شركة تقنية للذكاء الاصطناعي          | ar     | TECH      | societe  | NoorAI     | 71.0  | B    | 2026-06-18 11:50:00 |

-- ── Table feedback ─────────────────────────────────────────────────────────
-- | id | generation_id | vote_type | user_id | created_at          |
-- |----|---------------|-----------|---------|---------------------|
-- | 1  | 1             | like      | NULL    | 2026-06-18 12:00:00 |
-- | 2  | 1             | like      | NULL    | 2026-06-18 12:01:00 |
-- | 3  | 1             | like      | NULL    | 2026-06-18 12:02:00 |
-- | 4  | 2             | like      | NULL    | 2026-06-18 12:03:00 |
-- | 5  | 2             | dislike   | NULL    | 2026-06-18 12:04:00 |
-- | 6  | 3             | dislike   | NULL    | 2026-06-18 12:05:00 |
-- | 7  | 3             | dislike   | NULL    | 2026-06-18 12:06:00 |
-- | 8  | 3             | dislike   | NULL    | 2026-06-18 12:07:00 |
-- | 9  | 4             | like      | NULL    | 2026-06-18 12:08:00 |

-- Scores calculés (likes - dislikes) :
--   Veloria   : 3 - 0 = +3  (plus apprécié)
--   NeuraLink : 1 - 1 =  0
--   Solvita   : 0 - 3 = -3  (plus rejeté)
--   NoorAI    : 1 - 0 = +1

-- ── Table favoris ────────────────────────────────────────────────────────
-- | id | generation_id | user_id | nom     | langue | categorie | type_nom | created_at          |
-- |----|---------------|---------|---------|--------|-----------|----------|---------------------|
-- | 1  | 1             | NULL    | Veloria | fr     | LUXE      | marque   | 2026-06-18 12:10:00 |
-- | 2  | 4             | NULL    | NoorAI  | ar     | TECH      | societe  | 2026-06-18 12:11:00 |

-- ── Requêtes SQL utiles ──────────────────────────────────────────────────

-- Top 5 noms les plus appréciés :
SELECT g.id, g.nom_genere,
       SUM(CASE WHEN f.vote_type = 'like' THEN 1 ELSE 0 END) AS likes,
       SUM(CASE WHEN f.vote_type = 'dislike' THEN 1 ELSE 0 END) AS dislikes,
       SUM(CASE WHEN f.vote_type = 'like' THEN 1 ELSE 0 END)
         - SUM(CASE WHEN f.vote_type = 'dislike' THEN 1 ELSE 0 END) AS score
FROM generations g
LEFT JOIN feedback f ON f.generation_id = g.id
GROUP BY g.id
HAVING likes + dislikes > 0
ORDER BY score DESC
LIMIT 5;

-- Statistiques par langue :
SELECT g.langue,
       SUM(CASE WHEN f.vote_type = 'like' THEN 1 ELSE 0 END) AS likes,
       SUM(CASE WHEN f.vote_type = 'dislike' THEN 1 ELSE 0 END) AS dislikes
FROM generations g
JOIN feedback f ON f.generation_id = g.id
GROUP BY g.langue;
