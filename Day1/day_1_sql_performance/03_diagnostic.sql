/* PHASE 2 : DIAGNOSTIC
   Objectif : Identifier les lenteurs avant optimisation.
   Utiliser EXPLAIN ANALYZE devant chaque requête pour voir le plan.
*/

-- REQUÊTE 1 : Recherche simple sur du texte (Full Table Scan attendu)
-- "Trouver tous les étudiants dont le nom commence par 'Nam' et inscrits récemment"
EXPLAIN ANALYZE
SELECT * FROM students
WHERE last_name LIKE 'Name150%'
  AND registration_date > NOW() - INTERVAL '30 days';


-- REQUÊTE 2 : Jointure classique (Students + Enrollments + Courses)
-- "Récupérer les notes des étudiants en 'Math' avec un tri"
EXPLAIN ANALYZE
SELECT
    s.last_name,
    c.title,
    e.grade,
    e.enrollment_date
FROM enrollments e
JOIN students s ON e.student_id = s.student_id
JOIN courses c ON e.course_id = c.course_id
WHERE c.category = 'Math'
ORDER BY e.grade DESC
LIMIT 50;


-- REQUÊTE 3 : Agrégation et Statistiques (Gros calcul CPU/Mémoire)
-- "Moyenne des notes par catégorie de cours"
EXPLAIN ANALYZE
SELECT
    c.category,
    COUNT(e.student_id) as nb_students,
    AVG(e.grade) as average_grade
FROM enrollments e
JOIN courses c ON e.course_id = c.course_id
GROUP BY c.category
ORDER BY average_grade DESC;


-- REQUÊTE 4 : Analyse des Logs (La plus lourde !)
-- "Retrouver les logs d'accès des étudiants ayant eu une mauvaise note (< 20)"
EXPLAIN ANALYZE
SELECT
    s.email,
    a.url_accessed,
    a.access_time
FROM access_logs a
JOIN students s ON a.student_id = s.student_id
JOIN enrollments e ON s.student_id = e.student_id
WHERE e.grade < 20
  AND a.access_time > NOW() - INTERVAL '7 days'
LIMIT 100;


-- REQUÊTE 5 : Recherche de "Slow Queries" (Performance)
-- "Trouver tous les logs où le temps de réponse était critique (> 490ms) pour un cours donné"
EXPLAIN ANALYZE
SELECT student_id, url_accessed, duration_ms, access_time
FROM access_logs
WHERE duration_ms > 490
  AND url_accessed LIKE '/course/150/%'
ORDER BY access_time DESC;
