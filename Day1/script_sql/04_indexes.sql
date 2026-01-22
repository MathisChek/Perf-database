/* PHASE 3 : OPTIMISATION - CRÉATION DES INDEX
   Objectif : Remplacer les Seq Scan par des Index Scan pour les 5 requêtes.
*/

-- 1. Optimisation Requête 1 (Recherche par Nom)
-- Permet de trouver 'Name150%' sans lire toute la table
CREATE INDEX idx_students_lastname ON students(last_name);

-- 2. Optimisation Requête 2 (Jointures Étudiants/Cours)
-- Indispensable : Indexer les clés étrangères pour accélérer les JOIN
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);

-- Index pour le tri par note (ORDER BY grade)
CREATE INDEX idx_enrollments_grade ON enrollments(grade);

-- 3. Optimisation Requête 3 (Moyenne par catégorie)
-- Index couvrant : inclut la catégorie ET la note (INCLUDE)
CREATE INDEX idx_courses_category_grade ON courses(category) INCLUDE (title);
-- Note: L'optimisation max ici dépendrait aussi de la structure physique,
-- mais un index sur category aide déjà le GROUP BY.

-- 4. Optimisation Requête 4 (La "Catastrophe")
-- Index composite sur access_logs pour filtrer date ET faire la jointure
CREATE INDEX idx_logs_student_date ON access_logs(student_id, access_time);

-- 5. Optimisation Requête 5 (Slow Queries)
-- Index partiel ou composite pour filtrer rapidement sur la durée et l'URL
-- On indexe d'abord duration_ms car c'est le filtre le plus sélectif (> 490)
CREATE INDEX idx_logs_perf ON access_logs(duration_ms, url_accessed);

ANALYZE;
