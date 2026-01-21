import psycopg2
import time
from pymongo import MongoClient

# ================= CONFIGURATION =================

# 🐘 PostgreSQL
PG_CONFIG = {
    "host": "localhost",
    "port": "5433",
    "database": "pokedb",
    "user": "postgres",
    "password": "postgres"
}

# 🍃 MongoDB
# On garde la connexion qui a marché (Local + Admin Source)
MONGO_URI = "mongodb://etudiant:password@127.0.0.1:27017/?authSource=admin&directConnection=true"
MONGO_DB = "pokedb"
MONGO_COLL = "captures"

# ================= SCÉNARIOS =================
SCENARIOS = [
    {
        "name": "1. Recherche Exacte (Pikachu)",
        "sql": """
            EXPLAIN (ANALYZE, FORMAT JSON)
            SELECT c.trainer_name, c.capture_date, p.name
            FROM fact_captures c
            JOIN dim_pokemons p ON c.pokedex_id = p.pokedex_id
            WHERE p.name = 'pikachu';
        """,
        "mongo_filter": {"pokemon_details.name": "pikachu"},
        "mongo_type": "find"
    },
    {
        "name": "2. Intervalle (Lat > 45)",
        "sql": "EXPLAIN (ANALYZE, FORMAT JSON) SELECT * FROM fact_captures WHERE latitude > 45.0;",
        "mongo_filter": {"location.lat": {"$gt": 45.0}},
        "mongo_type": "find"
    },
    {
        "name": "3. Agrégation Simple (Count Météo)",
        "sql": "EXPLAIN (ANALYZE, FORMAT JSON) SELECT weather, COUNT(*) FROM fact_captures GROUP BY weather;",
        "mongo_pipeline": [{"$group": {"_id": "$weather", "count": {"$sum": 1}}}],
        "mongo_type": "aggregate"
    },
    {
        "name": "4. Complexe (Electric + Rainy)",
        "sql": """
            EXPLAIN (ANALYZE, FORMAT JSON)
            SELECT c.trainer_name FROM fact_captures c
            JOIN dim_pokemons p ON c.pokedex_id = p.pokedex_id
            WHERE p.type_1 = 'electric' AND c.weather = 'Rainy';
        """,
        "mongo_filter": {"pokemon_details.type_1": "electric", "weather": "Rainy"},
        "mongo_type": "find"
    },
    {
        "name": "5. Agrégation Lourde (Avg HP)",
        "sql": """
            EXPLAIN (ANALYZE, FORMAT JSON)
            SELECT c.weather, AVG(p.hp) FROM fact_captures c
            JOIN dim_pokemons p ON c.pokedex_id = p.pokedex_id
            GROUP BY c.weather;
        """,
        "mongo_pipeline": [{"$group": {"_id": "$weather", "avg_hp": {"$avg": "$pokemon_details.hp"}}}],
        "mongo_type": "aggregate"
    }
]

def run_benchmark():
    print("\n🚀 DÉMARRAGE DU BENCHMARK (SIMPLE)")
    print("===================================")

    # 1. Connexion SQL
    try:
        pg_conn = psycopg2.connect(**PG_CONFIG)
        pg_cursor = pg_conn.cursor()
    except Exception as e:
        print(f"❌ Erreur connexion PostgreSQL : {e}")
        return

    # 2. Connexion Mongo
    try:
        mongo_client = MongoClient(MONGO_URI)
        mongo_db = mongo_client[MONGO_DB]
        mongo_coll = mongo_db[MONGO_COLL]
        mongo_client.admin.command('ping')
    except Exception as e:
        print(f"❌ Erreur connexion MongoDB : {e}")
        return

    # 3. Boucle sur les tests
    for test in SCENARIOS:
        print(f"\n▶️  TEST : {test['name']}")

        # --- SQL ---
        try:
            pg_cursor.execute(test['sql'])
            explain = pg_cursor.fetchone()[0]
            t_sql = explain[0]['Plan']['Actual Total Time']
            print(f"   🐘 SQL   : {t_sql:.2f} ms")
        except Exception as e:
            print(f"   🐘 SQL   : Erreur ({e})")

        # --- MONGO ---
        try:
            t_mongo = 0
            if test['mongo_type'] == "find":
                expl = mongo_coll.find(test['mongo_filter']).explain()
                t_mongo = expl['executionStats']['executionTimeMillis']
            elif test['mongo_type'] == "aggregate":
                expl = mongo_db.command(
                    'explain',
                    {'aggregate': MONGO_COLL, 'pipeline': test['mongo_pipeline'], 'cursor': {}},
                    verbosity='executionStats'
                )
                # Gérer les structures de réponse variables
                stats = expl.get('executionStats')
                if not stats and 'stages' in expl:
                     stats = expl['stages'][0]['$cursor']['executionStats']
                t_mongo = stats['executionTimeMillis']

            print(f"   🍃 MONGO : {t_mongo} ms")
        except Exception as e:
            print(f"   🍃 MONGO : Erreur ({e})")

    pg_conn.close()
    mongo_client.close()
    print("\n✅ Terminé.")

if __name__ == "__main__":
    run_benchmark()
