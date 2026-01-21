-- 1. Pour la recherche "Pikachu"
CREATE INDEX idx_pokemon_name ON dim_pokemons(name);

-- 2. Pour la recherche "Latitude > 45"
CREATE INDEX idx_capture_lat ON fact_captures(latitude);

-- 3. Pour le Group By "Météo" (et le filtre Rainy)
CREATE INDEX idx_capture_weather ON fact_captures(weather);

-- 4. Pour le filtre "Type Electric"
CREATE INDEX idx_pokemon_type ON dim_pokemons(type_1);

-- 5. Optimisation de la jointure (FK) - Souvent critique
CREATE INDEX idx_capture_pokedex_id ON fact_captures(pokedex_id);
