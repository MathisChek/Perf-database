SELECT COUNT(*) FROM fact_captures;

SELECT COUNT(*) FROM dim_pokemons;

SELECT * FROM fact_captures LIMIT 5;

SELECT
    pg_size_pretty(pg_total_relation_size('fact_captures')) AS taille_table_captures,
    pg_size_pretty(pg_total_relation_size('dim_pokemons')) AS taille_dimension;
