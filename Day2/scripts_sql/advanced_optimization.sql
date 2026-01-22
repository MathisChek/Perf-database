-- PHASE 3 : OPTIMISATION AVANCÉE (Partitionnement & Vue Matérialisée)

-- 1. VUE MATÉRIALISÉE
-- Objectif : Pré-calculer la requête "Moyenne PV par météo" (Requête 5)
DROP MATERIALIZED VIEW IF EXISTS mv_weather_stats;

CREATE MATERIALIZED VIEW mv_weather_stats AS
SELECT
    c.weather,
    COUNT(*) as total_captures,
    AVG(p.hp) as avg_hp
FROM fact_captures c
JOIN dim_pokemons p ON c.pokedex_id = p.pokedex_id
GROUP BY c.weather;

-- Création d'un index sur la vue pour un accès instantané
CREATE INDEX idx_mv_weather ON mv_weather_stats(weather);


-- 2. PARTITIONNEMENT TEMPOREL
-- Objectif : Diviser la table fact_captures par année.
-- Note : PostgreSQL ne convertit pas une table simple en partitionnée directement.
-- Il faut créer une nouvelle table partitionnée et migrer les données.

-- A. Renommer l'ancienne table
ALTER TABLE fact_captures RENAME TO fact_captures_old;

-- B. Créer la table maître partitionnée (Même structure)
CREATE TABLE fact_captures (
    capture_id SERIAL,
    pokedex_id INT,
    trainer_name VARCHAR(50),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    capture_date TIMESTAMP,
    weather VARCHAR(20),
    PRIMARY KEY (capture_id, capture_date)
) PARTITION BY RANGE (capture_date);

-- C. Créer les partitions (Exemple : Archives vs Récent)
-- Partition pour les données anciennes (avant 2024)
CREATE TABLE captures_y2023 PARTITION OF fact_captures
    FOR VALUES FROM (MINVALUE) TO ('2024-01-01');

-- Partition pour les données récentes (2024 et après)
CREATE TABLE captures_y2024 PARTITION OF fact_captures
    FOR VALUES FROM ('2024-01-01') TO (MAXVALUE);

-- D. Migrer les données
INSERT INTO fact_captures (pokedex_id, trainer_name, latitude, longitude, capture_date, weather)
SELECT pokedex_id, trainer_name, latitude, longitude, capture_date, weather
FROM fact_captures_old;

-- E. Ré-appliquer les index sur la nouvelle table
CREATE INDEX idx_part_weather ON fact_captures(weather);
CREATE INDEX idx_part_lat ON fact_captures(latitude);
CREATE INDEX idx_part_pokemon ON fact_captures(pokedex_id);
