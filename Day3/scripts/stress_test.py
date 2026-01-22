import psycopg2
import threading
import time
import random
import os
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION MÉTÉO (Port 5434) ---
DB_CONFIG = {
  "host": "localhost",
  "port": "5434",
  "database": "weather_db",
  "user": "meteo_user",
  "password": "password"
}

# --- REQUÊTES pour stresser la base et la machine ---
# On fait des calculs pour faire travailler le CPU (AVG, MAX, GROUP BY)
QUERIES = [
  "SELECT city, AVG(temperature), MAX(humidity) FROM weather_measures GROUP BY city",

  "SELECT * FROM weather_measures WHERE temperature > 15 AND humidity < 80",

  "SELECT * FROM weather_measures ORDER BY recorded_at DESC LIMIT 100",

  "SELECT COUNT(*) FROM weather_measures"
]

def run_stress(thread_id):
  try:
    # On crée une nouvelle connexion pour chaque thread
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print(f"🚀 Thread {thread_id} prêt à spammer...")

    while True:
      q = random.choice(QUERIES)

      # Exécution
      cur.execute(q)
      # Force la lecture des résultats pour charger la RAM/Réseau
      cur.fetchall()

  except Exception as e:
    print(f"❌ Erreur Thread {thread_id}: {e}")
    time.sleep(1)

if __name__ == "__main__":
  print("="*50)
  print("💣 DÉMARRAGE DU STRESS TEST MÉTÉO (Port 5434)")
  print("Regarde ton Grafana : CPU et Transactions/sec vont monter !")
  print("="*50)

  # On lance 10 processus en parallèle pour simuler 10 utilisateurs
  threads = []
  for i in range(10):
    t = threading.Thread(target=run_stress, args=(i,))
    t.start()
    threads.append(t)

  # Garde le script en vie
  for t in threads:
      t.join()
