/* FICHIER : mongo_queries.js
   BUT : Stocker les requêtes de test pour le comparatif NoSQL
   USAGE : Copier le contenu de "Filter" ou "Pipeline" dans MongoDB Compass
*/

// ==========================================
// 1. RECHERCHE EXACTE (Pikachu)
// ==========================================
// Type : FILTER
// Dans Compass : Onglet "Documents" > Barre "Filter"
{ "pokemon_details.name": "pikachu" }


// ==========================================
// 2. RECHERCHE INTERVALLE (Latitude > 45)
// ==========================================
// Type : FILTER
// Dans Compass : Onglet "Documents" > Barre "Filter"
{ "location.lat": { "$gt": 45.0 } }


// ==========================================
// 3. AGRÉGATION SIMPLE (Compter par Météo)
// ==========================================
// Type : AGGREGATION
// Dans Compass : Onglet "Aggregations" > Stage 1 ($group)
{
    "_id": "$weather",
    "count": { "$sum": 1 }
}


// ==========================================
// 4. RECHERCHE COMPLEXE (Electric + Rainy)
// ==========================================
// Type : FILTER
// Dans Compass : Onglet "Documents" > Barre "Filter"
{
    "pokemon_details.type_1": "electric",
    "weather": "Rainy"
}


// ==========================================
// 5. AGRÉGATION LOURDE (Moyenne HP / Météo)
// ==========================================
// Type : AGGREGATION
// Dans Compass : Onglet "Aggregations" > Stage 1 ($group)
{
    "_id": "$weather",
    "avg_hp": { "$avg": "$pokemon_details.hp" }
}
