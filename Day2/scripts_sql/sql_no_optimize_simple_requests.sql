/* FICHIER : queries_analysis.sql
   BUT : Comparatif de performance SQL vs NoSQL (Phase Lecture)
   CONTEXTE : Base "pokeDB" (PostgreSQL) - 500 000 lignes

   INSTRUCTIONS :
   Exécuter chaque requête une par une et noter le temps d'exécution (Execution Time).
   Comparer ensuite avec les temps obtenus sur MongoDB pour les mêmes scénarios et pouvoir comparer une fois la base de données optimisée.
*/

-- =========================================================
-- 1. RECHERCHE EXACTE (Point Query)
-- =========================================================
-- Scénario : "Trouver toutes les captures de Pikachu."
-- Défi SQL : Doit faire une JOINTURE car le nom 'pikachu' est dans la table dimension.
-- Défi NoSQL : Lecture directe d'un champ imbriqué (pokemon_details.name).

EXPLAIN ANALYZE
SELECT
    c.trainer_name,
    c.capture_date,
    p.name
FROM fact_captures c
JOIN dim_pokemons p ON c.pokedex_id = p.pokedex_id
WHERE p.name = 'pikachu';


-- =========================================================
-- 2. FILTRAGE SUR INTERVALLE (Range Query)
-- =========================================================
-- Scénario : "Trouver les captures faites dans l'Hémisphère Nord (Lat > 45)."
-- Défi : Scan séquentiel sur une colonne numérique (FLOAT/DECIMAL).

EXPLAIN ANALYZE
SELECT * FROM fact_captures
WHERE latitude > 45.0;


-- =========================================================
-- 3. AGRÉGATION SIMPLE (Group By)
-- =========================================================
-- Scénario : "Compter le nombre de captures par type de météo."
-- Défi : Le moteur doit parcourir toute la table pour compter (Full Table Scan).

EXPLAIN ANALYZE
SELECT
    weather,
    COUNT(*) as total_captures
FROM fact_captures
GROUP BY weather;


-- =========================================================
-- 4. FILTRE COMPLEXE MULTI-CRITÈRES
-- =========================================================
-- Scénario : "Trouver les Pokémon 'Electric' capturés par temps 'Rainy'."
-- Défi : Double filtre nécessitant une jointure (Type dans dim_pokemons, Météo dans fact_captures).

EXPLAIN ANALYZE
SELECT
    c.trainer_name,
    p.name as pokemon_name,
    c.weather
FROM fact_captures c
JOIN dim_pokemons p ON c.pokedex_id = p.pokedex_id
WHERE p.type_1 = 'electric'
  AND c.weather = 'Rainy';


-- =========================================================
-- 5. AGRÉGATION LOURDE (Statistiques avec Jointure)
-- =========================================================
-- Scénario : "Moyenne des Points de Vie (HP) des Pokémon capturés par Météo."
-- Défi : Très coûteux. Doit joindre 500k lignes, récupérer une valeur (HP) et calculer la moyenne.

EXPLAIN ANALYZE
SELECT
    c.weather,
    AVG(p.hp) as avg_hp
FROM fact_captures c
JOIN dim_pokemons p ON c.pokedex_id = p.pokedex_id
GROUP BY c.weather;
