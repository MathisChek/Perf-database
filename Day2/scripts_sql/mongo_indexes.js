// PHASE 4 : OPTIMISATION MONGODB
// À lancer dans Mongosh ou Compass

// 1. Index Simple (Requis par le sujet)
// Optimise la recherche par nom de Pokemon
db.captures.createIndex({ "pokemon_details.name": 1 });

// 2. Index Composé (Requis par le sujet)
// Optimise la requête complexe "Type Electric + Météo Rainy"
db.captures.createIndex({ "pokemon_details.type_1": 1, "weather": 1 });

// 3. Index pour les Tris/Plages
db.captures.createIndex({ "location.lat": 1 });
db.captures.createIndex({ "weather": 1 });

print("✅ Index MongoDB créés avec succès !");

// Note pour le rapport :
// Utiliser db.captures.find(...).explain("executionStats")
// Comparer "totalDocsExamined" avant (500000) et après (quelques dizaines).
