import requests
import time
import random
import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from pymongo import MongoClient
from datetime import datetime
from faker import Faker

# Cherger les variables d'ENV
load_dotenv()

print(f"👀 DEBUG URI: {os.getenv('MONGO_URI')}")

# --- MONGO ATLAS ---
ATLAS_URI = os.getenv("MONGO_URI")

if not ATLAS_URI:
    print("❌ ERREUR : Variable 'MONGO_URI' introuvable dans le fichier .env")
    exit()

# ==========================================
# 1. CONFIGURATION
# ==========================================
TOTAL_EVENTS = 500000    # Objectif : 500 000 lignes
BATCH_SIZE = 5000        # Taille des paquets


# --- POSTGRES LOCAL ---
PG_CONFIG = {
    "dbname": "pokedb",  # <--- On tape dans la base créée sur Beekeeper
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    "host": "localhost",
    "port": "5433"
}

fake = Faker()

# ==========================================
# 2. LOGS & CONNEXIONS
# ==========================================
print("\n" + "="*50)
print("🚀 DÉMARRAGE DU PROTOCOLE D'INGESTION POKEDB")
print("="*50 + "\n")

# --- TEST API ---
print("📡 1. Test connexion API PokéAPI...", end=" ")
try:
    r = requests.get("https://pokeapi.co/api/v2/pokemon/1", timeout=5)
    if r.status_code == 200:
        print("✅ SUCCÈS (API répond)")
    else:
        print(f"❌ ERREUR API (Code {r.status_code})")
        exit()
except Exception as e:
    print(f"❌ ÉCHEC : {e}")
    exit()

# --- TEST MONGO ---
print("🍃 2. Test connexion MongoDB Atlas (pokeDB)...", end=" ")
try:
    mongo_client = MongoClient(ATLAS_URI)
    mongo_client.admin.command('ping') # Force le ping
    mongo_db = mongo_client["pokedb"]  # <--- Nom unifié
    mongo_col = mongo_db["captures"]
    mongo_col.delete_many({}) # On nettoie pour être sûr
    print("✅ SUCCÈS (Connecté et nettoyé)")
except Exception as e:
    print(f"\n❌ ERREUR MONGO : {e}")
    exit()

# --- TEST POSTGRES ---
print("🐘 3. Test connexion PostgreSQL (pokeDB)...", end=" ")
try:
    pg_conn = psycopg2.connect(**PG_CONFIG)
    pg_cursor = pg_conn.cursor()
    print("✅ SUCCÈS (Base trouvée)")
except Exception as e:
    print(f"\n❌ ERREUR POSTGRES : {e}")
    print("Astuce : Vérifie que la base 'pokeDB' est bien créée dans Beekeeper.")
    exit()

# ==========================================
# 3. SCHEMA SQL
# ==========================================
print("\n🛠️  4. Initialisation du schéma SQL...")
pg_cursor.execute("DROP TABLE IF EXISTS fact_captures;")
pg_cursor.execute("DROP TABLE IF EXISTS dim_pokemons;")

pg_cursor.execute("""
    CREATE TABLE dim_pokemons (
        pokedex_id INT PRIMARY KEY,
        name VARCHAR(50),
        type_1 VARCHAR(20),
        hp INT,
        attack INT
    );
""")
pg_cursor.execute("""
    CREATE TABLE fact_captures (
        capture_id SERIAL PRIMARY KEY,
        pokedex_id INT REFERENCES dim_pokemons(pokedex_id),
        trainer_name VARCHAR(50),
        latitude DECIMAL(9,6),
        longitude DECIMAL(9,6),
        capture_date TIMESTAMP,
        weather VARCHAR(20)
    );
""")
pg_conn.commit()
print("✅ Tables 'dim_pokemons' et 'fact_captures' créées.")

# ==========================================
# 4. IMPORT API
# ==========================================
print("\n📥 5. Téléchargement du référentiel Pokémon (API)...")
pokemon_ref = []

for i in range(1, 152):
    try:
        r = requests.get(f"https://pokeapi.co/api/v2/pokemon/{i}")
        d = r.json()

        # Extraction
        stats = {s['stat']['name']: s['base_stat'] for s in d['stats']}
        types = [t['type']['name'] for t in d['types']]

        p_obj = {
            "id": d['id'],
            "name": d['name'],
            "type_1": types[0],
            "hp": stats.get('hp'),
            "attack": stats.get('attack'),
            "sprite": d['sprites']['front_default']
        }
        pokemon_ref.append(p_obj)

        # Insertion SQL Dimension
        pg_cursor.execute("""
            INSERT INTO dim_pokemons (pokedex_id, name, type_1, hp, attack)
            VALUES (%s, %s, %s, %s, %s)
        """, (p_obj['id'], p_obj['name'], p_obj['type_1'], p_obj['hp'], p_obj['attack']))

    except Exception as e:
        print(f"⚠️ Erreur sur Pokemon {i}: {e}")

pg_conn.commit()
print(f"✅ Référentiel chargé : {len(pokemon_ref)} Pokémon stockés.")

# ==========================================
# 5. GENERATION MASSIVE
# ==========================================
print(f"\n⚡ 6. Génération et Injection des {TOTAL_EVENTS} captures...")
print("   (Cela va prendre quelques instants...)")

start_time = time.time()
generated = 0
weathers = ['Sunny', 'Rainy', 'Cloudy', 'Snow', 'Windy']

while generated < TOTAL_EVENTS:
    batch_mongo = []
    batch_sql = []

    for _ in range(BATCH_SIZE):
        # Simulation Faker
        pk = random.choice(pokemon_ref)
        trainer = fake.first_name()
        lat, lon = float(fake.latitude()), float(fake.longitude())
        date = datetime.now()
        weather = random.choice(weathers)

        # Mongo (Document riche)
        doc_mongo = {
            "pokemon_details": pk,
            "trainer": trainer,
            "location": {"lat": lat, "lon": lon},
            "timestamp": date,
            "weather": weather
        }
        batch_mongo.append(doc_mongo)

        # SQL (Relationnel plat)
        row_sql = (pk['id'], trainer, lat, lon, date, weather)
        batch_sql.append(row_sql)

    # Insertions Bulk
    mongo_col.insert_many(batch_mongo)

    q_sql = "INSERT INTO fact_captures (pokedex_id, trainer_name, latitude, longitude, capture_date, weather) VALUES %s"
    execute_values(pg_cursor, q_sql, batch_sql)
    pg_conn.commit()

    generated += BATCH_SIZE
    # Log de progression
    if generated % 50000 == 0:
        print(f"   📊 Progression : {generated} / {TOTAL_EVENTS} lignes...")

duration = time.time() - start_time

print("\n" + "="*50)
print("✅ TERMINÉ ! TOUT EST VERT.")
print(f"⏱️ Temps total génération : {duration:.2f} sec")
print("="*50)

pg_cursor.close()
pg_conn.close()
mongo_client.close()
