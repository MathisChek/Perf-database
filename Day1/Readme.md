# 📊 Rapport Audit & Optimisation PostgreSQL (Jour 1)

Ce rapport analyse les performances d'une base de données E-learning (200k étudiants, 5M logs) et détaille les stratégies d'optimisation mises en place.

---

## 1. Conception & Choix des Types de Données

Le schéma relationnel a été conçu pour garantir l'intégrité des données tout en optimisant l'espace disque. Voici la justification des types choisis pour les colonnes critiques :

| Champ | Type Choisi | Justification Technique |
|-------|-------------|-------------------------|
| Identifiants (`_id`) | `SERIAL` (INT) | Standard PostgreSQL. L'entier (4 bytes) est plus performant pour les jointures et l'indexation B-Tree que des UUID. |
| Noms / Emails | `VARCHAR(N)` | Permet de définir une limite logique métier (intégrité) contrairement au type `TEXT`, sans surcoût de performance notable. |
| Dates | `TIMESTAMP` | Nécessaire pour des calculs précis de durée (`access_logs`) et d'ancienneté, impossible avec un simple `DATE`. |
| Durée (`duration_ms`) | `INT` | Suffisant pour stocker des millisecondes. Moins lourd qu'un `FLOAT` ou `INTERVAL` pour des agrégations simples. |
| Note (`grade`) | `INT` | Stockage optimisé. Une contrainte `CHECK (0-100)` assure la validité métier. |

---

## 2. Résultats : Impact de l'Indexation

Les mesures suivantes comparent les temps d'exécution (`Execution Time`) avant et après création des index.

> Les plans d'exécution ont été validés via `EXPLAIN (ANALYZE, BUFFERS)` pour confirmer la réduction des accès disques.

| Requête | Temps AVANT (Seq Scan) | Temps APRÈS (Index Scan) | Gain |
|---------|------------------------|--------------------------|------|
| 1. Recherche Nom | 25 ms | 23 ms | ✅ +8,0 % |
| 2. Recherche Notes (Jointure) | 519 ms | 529 ms | ❌ -1,9 % |
| 3. Moyenne par catégorie | 403 ms | 403 ms | ⚠️ 0,0 % |
| 4. Analyse Logs (Complexe) | 4922 ms | 3709 ms | ✅ +24,6 % |
| 5. Slow Queries (Critique) | 187 ms | 246 ms | ❌ -31,6 % |

---

## 3. Analyse Approfondie

### ✅ Le Succès (Requête 4)

Le gain de **1.2s** sur l'analyse des logs valide la stratégie de l'index composite. L'analyse des buffers montre que nous sommes passés d'une lecture massive du disque (`Buffers Read`) à des accès mémoire ciblés (`Shared Hit`), grâce au filtrage combiné sur la date et l'étudiant.

### ⚠️ Le Paradoxe de la Régression (Requêtes 2 & 5)

Nous observons une **perte de performance** (-31% sur la requête 5).

**Cause** : L'absence de clause `LIMIT` oblige la base à récupérer un volume massif de lignes (faible sélectivité).

**Explication** : Lire toute la table en continu (Sequential Scan) est physiquement plus rapide pour le disque que de faire des millions de sauts d'index (Random Access) pour récupérer les lignes une par une. Ici, l'index génère un surcoût d'I/O inutile.

---

## 4. Correction de la Requête Mal Conçue

La Requête 5 ("Slow Queries") a été identifiée comme **mal conçue** car elle tente de trier des millions de lignes sans limite, rendant l'index contre-productif.

**Correction Proposée** : Ajout d'un `LIMIT` pour bénéficier du tri de l'index.

```sql
SELECT student_id, url_accessed, duration_ms, access_time
FROM access_logs
WHERE duration_ms > 490
ORDER BY access_time DESC
LIMIT 50; -- <--- L'optimisation clé
```

**Impact de la correction** :

Avec cet ajout, le plan d'exécution bascule sur un **Index Scan Backward**. Le moteur s'arrête dès qu'il a trouvé les 50 logs les plus récents correspondant au critère, rendant la requête quasi-instantanée (**< 5ms**) contre 246ms auparavant.

---

## 🔧 Annexe : Stratégie d'Indexation Détaillée

Le fichier `sql/04_indexes.sql` contient les instructions DDL. Voici la justification technique :

### `idx_students_lastname` (B-Tree)

* **Cible** : `students(last_name)`
* **Objectif** : Optimise la recherche textuelle (Req 1)

### `idx_enrollments_student` / `idx_enrollments_course`

* **Cible** : Index sur clés étrangères
* **Objectif** : Indispensable pour éviter les Hash Joins coûteux lors des jointures (Req 2)

### `idx_courses_category_grade` (Covering Index)

* **Cible** : `category` + `INCLUDE(title)`
* **Objectif** : Permet un **Index Only Scan** pour les agrégations (Req 3), évitant de lire la table physique

### `idx_logs_student_date` (Composite)

* **Cible** : `(student_id, access_time)`
* **Objectif** : Réduit drastiquement le scope de recherche pour l'historique étudiant (Req 4)

### `idx_logs_perf` (Composite)

* **Cible** : `(duration_ms, url_accessed)`
* **Objectif** : Place la colonne la plus sélective en premier pour filtrer les lenteurs (Req 5)
