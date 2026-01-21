-- 1. Pour accélérer le GROUP BY city (Moyennes par ville)
CREATE INDEX idx_weather_city ON weather_measures(city);

-- 2. Pour accélérer le filtrage par Température et Humidité (WHERE temp > X AND hum < Y)
CREATE INDEX idx_weather_temp_hum ON weather_measures(temperature, humidity);

-- 3. Pour accélérer le tri chronologique (ORDER BY recorded_at DESC)
CREATE INDEX idx_weather_date ON weather_measures(recorded_at DESC);
