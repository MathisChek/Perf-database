import os
import time
import requests
import psycopg2
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
API_KEY = os.getenv("OPENWEATHER_API_KEY")
CITIES = ["Paris", "London", "New York", "Tokyo", "Bordeaux", "Sydney", "Moscow"]
DB_CONFIG = {
	"host": os.getenv("DB_HOST", "localhost"),
	"port": os.getenv("DB_PORT", "5434"),
	"database": os.getenv("DB_NAME", "weather_db"),
	"user": os.getenv("DB_USER", "meteo_user"),
	"password": os.getenv("DB_PASSWORD", "password")
}

# --- OUTILS ---
def log(msg, type="INFO"):
	"""Affiche un log formaté avec l'heure"""
	emoji = "ℹ️ "
	if type == "ERROR": emoji = "❌"
	elif type == "SUCCESS": emoji = "✅"
	elif type == "WARN": emoji = "⚠️ "

	timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	print(f"[{timestamp}] {emoji} {msg}")

# --- VÉRIFICATIONS PRÉALABLES ---
def test_api_connection():
	"""Vérifie si la clé API fonctionne en interrogeant une ville test"""
	log("Test de connexion à l'API OpenWeatherMap...", "INFO")
	test_url = f"http://api.openweathermap.org/data/2.5/weather?q=Paris&appid={API_KEY}&units=metric"

	try:
			response = requests.get(test_url, timeout=5)
			if response.status_code == 200:
					log("Connexion API réussie !", "SUCCESS")
					return True
			elif response.status_code == 401:
					log("Erreur API : Clé invalide (Unauthorized). Vérifiez votre .env", "ERROR")
					return False
			else:
					log(f"Erreur API : Code {response.status_code}", "ERROR")
					return False
	except requests.exceptions.ConnectionError:
			log("Impossible de joindre api.openweathermap.org (Pas d'internet ?)", "ERROR")
			return False
	except Exception as e:
			log(f"Erreur inattendue API : {e}", "ERROR")
			return False

def wait_for_db():
	"""Tente de se connecter à la base en boucle jusqu'à succès"""
	log(f"Test de connexion à PostgreSQL ({DB_CONFIG['host']}:{DB_CONFIG['port']})...", "INFO")

	max_retries = 10
	for i in range(max_retries):
			try:
					conn = psycopg2.connect(**DB_CONFIG)
					conn.close()
					log("Connexion PostgreSQL réussie !", "SUCCESS")
					return True
			except psycopg2.OperationalError as e:
					log(f"La base n'est pas encore prête... (Tentative {i+1}/{max_retries})", "WARN")
					time.sleep(2)

	log("Abandon : Impossible de se connecter à PostgreSQL après plusieurs essais.", "ERROR")
	return False

def init_db():
	"""Crée la table si elle n'existe pas"""
	try:
			conn = psycopg2.connect(**DB_CONFIG)
			cur = conn.cursor()
			cur.execute("""
					CREATE TABLE IF NOT EXISTS weather_measures (
							id SERIAL PRIMARY KEY,
							city VARCHAR(50),
							temperature FLOAT,
							humidity INT,
							pressure INT,
							description VARCHAR(100),
							recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
					);
			""")
			conn.commit()
			cur.close()
			conn.close()
			log("Structure de la base vérifiée (Table 'weather_measures').", "SUCCESS")
	except Exception as e:
			log(f"Erreur lors de la création de la table : {e}", "ERROR")
			sys.exit(1)

# --- CŒUR DU SCRIPT ---
def run_collection():
	print("\n" + "="*50)
	print("🚀 WEATHER DATA COLLECTOR - INITIALISATION")
	print("="*50)

	# 1. Vérifications bloquantes
	if not API_KEY:
		log("Variable OPENWEATHER_API_KEY manquante dans le .env", "ERROR")
		sys.exit(1)

	print(f"DEBUG: Clé lue = '{API_KEY}'")
	if not test_api_connection():
		log("Arrêt du script : API inaccessible.", "ERROR")
		sys.exit(1)

	if not wait_for_db():
		sys.exit(1)

	init_db()

	# 3. Boucle infinie pour la collecte de données en temps réel
	print("\n" + "="*50)
	print("📡 DÉMARRAGE DE LA COLLECTE (Ctrl+C pour arrêter)")
	print("="*50)

	while True:
		try:
			conn = psycopg2.connect(**DB_CONFIG)
			cur = conn.cursor()

			start_time = time.time()
			success_count = 0

			for city in CITIES:
				url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

				try:
					r = requests.get(url, timeout=3)
					if r.status_code == 200:
						data = r.json()
						temp = data['main']['temp']
						hum = data['main']['humidity']
						press = data['main']['pressure']
						desc = data['weather'][0]['description']

						cur.execute("""
								INSERT INTO weather_measures (city, temperature, humidity, pressure, description)
								VALUES (%s, %s, %s, %s, %s)
						""", (city, temp, hum, press, desc))

						# Affichage compact
						print(f"📍 {city:<10} | {temp:>5.1f}°C | 💧 {hum}%")
						success_count += 1
					else:
						log(f"Erreur données pour {city}: {r.status_code}", "WARN")

				except Exception as req_err:
					log(f"Erreur requête pour {city}: {req_err}", "WARN")

			conn.commit()
			cur.close()
			conn.close()

			# Log de fin de cycle
			elapsed = time.time() - start_time
			log(f"Cycle terminé. {success_count}/{len(CITIES)} villes mises à jour en {elapsed:.2f}s.", "INFO")

			# Pause de 10s
			print("💤 Attente 10s...")
			time.sleep(10)

		except KeyboardInterrupt:
			print("\n🛑 Arrêt manuel du script. Au revoir !")
			sys.exit(0)
		except Exception as e:
			log(f"Erreur critique dans la boucle principale : {e}", "ERROR")
			log("Nouvelle tentative dans 10 secondes...", "WARN")
			time.sleep(10)

if __name__ == "__main__":
  run_collection()
