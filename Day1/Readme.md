## 📊 Résultats : Impact de l'Indexation (PostgreSQL)

Voici les mesures de performance réalisées avant et après la création des index B-Tree.
Les tests ont été effectués sans clause `LIMIT` sur des requêtes retournant un grand volume de données.

| Requête | Temps AVANT (Seq Scan) | Temps APRÈS (Index Scan) | Gain (%) |
| :--- | :--- | :--- | :--- |
| **1. Recherche Nom** | 25 ms | 23 ms | <span style="color:green">**+ 8,0 %**</span> |
| **2. Recherche Notes (Jointure)** | 519 ms | 529 ms | <span style="color:red">**- 1,9 %**</span> |
| **3. Moyenne par catégorie** | 403 ms | 403 ms | <span style="color:orange">**0,0 %**</span> |
| **4. Analyse Logs (Complexe)** | 4922 ms | 3709 ms | <span style="color:green">**+ 24,6 %**</span> |
| **5. Slow Queries (Critique)** | 187 ms | 246 ms | <span style="color:red">**- 31,6 %**</span> |

### 🧐 Analyse et Conclusion

Ces résultats mettent en évidence une règle fondamentale des bases de données : **la Sélectivité**.

1.  **Le Paradoxe de la Régression (Requêtes 2 & 5)** :
    * Nous observons une perte de performance (-31% sur la requête 5).
    * **Cause :** L'absence de `LIMIT` oblige la base à récupérer un très grand nombre de lignes (faible sélectivité).
    * **Explication :** Lire toute la table en continu (*Sequential Scan*) est physiquement plus rapide pour le disque que de faire des millions de sauts d'index (*Random Access*) pour récupérer les lignes une par une. L'index devient ici une charge supplémentaire inutile.

2.  **Le Gain sur la Charge Lourde (Requête 4)** :
    * Gain significatif de **~1.2s** sur la requête la plus lourde.
    * Ici, l'index composite a permis d'éviter de scanner inutilement des millions de logs hors de la plage de date, prouvant l'efficacité de l'indexation sur le filtrage volumétrique.

3.  **Conclusion Générale** :
    * Les index sont redoutables pour des recherches précises (ex: trouver *un* étudiant spécifique).
    * Pour des requêtes analytiques larges (ex: moyennes, listes complètes), le moteur privilégie souvent le scan complet.
    * **L'optimisation idéale** aurait nécessité l'ajout de clauses `LIMIT` ou de filtres plus restrictifs pour bénéficier pleinement de la structure en arbre des index.

---

## 🔧 Annexe : Détail de la Stratégie d'Indexation

Le fichier `sql/04_indexes.sql` contient les instructions DDL pour optimiser spécifiquement les 5 requêtes diagnostiquées. Voici la justification technique de chaque index créé :

* **`idx_students_lastname`** (B-Tree standard)
    * **Cible :** Table `students`, colonne `last_name`.
    * **Objectif :** Accélérer la Requête 1 (Recherche textuelle) en évitant le scan complet des 200 000 étudiants.

* **`idx_enrollments_student`** & **`idx_enrollments_course`**
    * **Cible :** Table `enrollments`, clés étrangères `student_id` et `course_id`.
    * **Objectif :** Optimiser les jointures (`JOIN`) critiques de la Requête 2. Sans ces index, PostgreSQL doit souvent effectuer des *Hash Joins* coûteux en mémoire.

* **`idx_enrollments_grade`**
    * **Cible :** Table `enrollments`, colonne `grade`.
    * **Objectif :** Supprimer l'étape de tri explicite (*Sort Key*) de la Requête 2 (`ORDER BY grade`), l'index étant déjà trié naturellement.

* **`idx_courses_category_grade`** (Index Couvrant / *Covering Index*)
    * **Cible :** Table `courses`, colonne `category` (avec `INCLUDE title`).
    * **Objectif :** Permettre un *Index Only Scan* pour la Requête 3 (Agrégation). Le moteur peut récupérer la catégorie sans jamais lire la table physique (Heap), économisant des I/O disques.

* **`idx_logs_student_date`** (Index Composite)
    * **Cible :** Table `access_logs`, colonnes `(student_id, access_time)`.
    * **Objectif :** Traiter la Requête 4 ("La Catastrophe"). La combinaison permet de filtrer la date ET de faire la jointure avec l'étudiant en une seule opération d'index, réduisant drastiquement le nombre de lignes lues.

* **`idx_logs_perf`** (Index Composite Sélectif)
    * **Cible :** Table `access_logs`, colonnes `(duration_ms, url_accessed)`.
    * **Objectif :** Identifier instantanément les requêtes lentes (Requête 5). La colonne `duration_ms` est placée en premier car le filtre `> 490` est très sélectif.
