# 🌦️ Jour 3 : Monitoring Temps Réel & Optimisation SQL

Ce projet finalise le cycle de TPs en mettant en place une infrastructure de monitoring complète (type DevOps/SRE) pour surveiller une base de données PostgreSQL en production.

---

## 💡 Pourquoi une API Météo ?

Contrairement aux TPs précédents basés sur des données statiques (Pokémon), nous avons choisi ici d'utiliser l'API **OpenWeatherMap**. Cela nous permet de manipuler de la **donnée vivante** (Time Series) qui évolue dans le temps, offrant un scénario réaliste pour observer des courbes de température et d'humidité en temps réel sur Grafana.

---

## 🏗️ Architecture Technique

L'infrastructure repose sur **5 services interconnectés** via Docker :

| Service | Rôle | Port |
|---------|------|------|
| 🐍 **Python Worker** | Robot d'ingestion qui interroge l'API toutes les 60s | - |
| 🐘 **PostgreSQL** | Base de données de stockage (`weather_db`) | 5434 |
| 🕵️‍♂️ **Postgres Exporter** | Sonde qui expose les métriques techniques de la DB | 9187 |
| 💾 **Prometheus** | Base de données temporelle pour l'historique des métriques | 9090 |
| 📊 **Grafana** | Interface de visualisation (Dashboards & Alerting) | 3000 |

---

## 📂 Structure du Projet

```
Day3/
├── docker-compose.yml       # Orchestration des conteneurs
├── Dockerfile               # Configuration image
├── prometheus.yml           # Config du scraping Prometheus
├── requirements.txt         # Dépendances Python
├── .env                     # Variables d'environnement (Clés API, DB)
├── scripts/
│   ├── weather_collector.py # Script d'ingestion météo (Live)
│   ├── stress_test.py       # Script de simulation de charge
│   └── indexes.sql          # Requêtes d'optimisation
└── images/                  # Captures d'écran pour le README
```

---

## 🚀 Guide de Démarrage

### 1. Pré-requis & Outils

* **Docker** & Docker Compose (v3.8+)
* **Python 3.10+** (pour lancer les scripts clients)
* **Clé API OpenWeatherMap** (Gratuite)
* **Beekeeper Studio** (ou DBeaver) pour l'accès SQL

### 2. Installation

Clonez le dépôt et installez les dépendances Python :

```bash
cd Day3
pip install -r requirements.txt
```

### 3. Configuration (.env)

Assurez-vous que le fichier `.env` est présent à la racine du dossier `Day3` :

```ini
OPENWEATHER_API_KEY=votre_cle_api_ici
DB_HOST=localhost
DB_PORT=5434
DB_NAME=weather_db
DB_USER=meteo_user
DB_PASSWORD=password
```

### 4. Lancement de l'Infrastructure

Démarrez la stack de monitoring (Postgres + Prometheus + Grafana) :

```bash
docker-compose up -d
```

| Interface | URL | Identifiants |
|-----------|-----|--------------|
| Grafana | http://localhost:3000 | `admin` / `admin` |
| Prometheus | http://localhost:9090 | - |

### 5. Lancement de l'Ingestion

Démarrez le collecteur pour commencer à remplir la base :

```bash
python3 scripts/weather_collector.py
```

### 6. Lancement du Test de Charge (Optionnel)

Pour simuler une charge réaliste et observer l'impact sur les métriques Grafana, lancez le script de stress :

```bash
python3 scripts/stress_test.py
```

Ce script simule **10 utilisateurs simultanés** qui exécutent des requêtes lourdes (agrégations, tris, jointures) en boucle. C'est ce qui permet de visualiser les pics de charge sur le dashboard et de valider l'efficacité des index.

---

## 🧪 Le TP : Scénario "Chaos & Optimisation"

L'objectif était de prouver l'efficacité du monitoring pour **détecter et résoudre** des problèmes de performance.

### Étape 1 : Création de la Charge (Le Problème)

Nous avons lancé le script `scripts/stress_test.py` qui simule **10 utilisateurs simultanés** effectuant des requêtes lourdes (agrégations, tris complets) sans aucun index.

> ⚠️ **Note importante sur le Volume de Données**
>
> Pour observer une différence significative sur les graphiques, le volume de données est critique. Avec seulement quelques milliers de lignes, PostgreSQL est trop rapide (tout tient en RAM) et les index sont inutiles. Pour ce TP, nous avons dû injecter **500 000 lignes** de fausses données (via `generate_series`) pour saturer le CPU et rendre les index indispensables.

### Étape 2 : L'Optimisation (La Solution)

Sous la charge, nous avons appliqué les index suivants (disponibles dans `scripts/indexes.sql`) :

```sql
CREATE INDEX idx_weather_city ON weather_measures(city);
CREATE INDEX idx_weather_date ON weather_measures(recorded_at DESC);
CREATE INDEX idx_weather_temp_hum ON weather_measures(temperature, humidity);
```

> **Note** : L'index composite `idx_weather_temp_hum` est particulièrement utile pour les requêtes analytiques qui filtrent ou agrègent sur les deux colonnes météo principales (ex: `WHERE temperature > 20 AND humidity < 80`).

### Étape 3 : Résultats (La Preuve)

Le dashboard Grafana ci-dessous montre l'impact immédiat de l'optimisation :

![Dashboard Grafana - Avant/Après optimisation](images/Capture_Graphana.png)

**Observations clés :**

| Métrique | Zone "Avant" | Zone "Après" |
|----------|--------------|--------------|
| **CPU Time** | ~5.2s (en hausse) | ~200ms (chute brutale) |
| **Active Sessions** | 4-6 sessions bloquées | ~2 sessions (quasi idle) |
| **Transactions/sec** | ~10 TPS | ~60 TPS (x6 !) |

Le serveur traite **plus de requêtes avec moins d'effort** après l'application des index.

---

## 🔔 Bonus : Alerting Automatique (3 Règles)

Pour garantir la stabilité de la production, nous avons configuré **3 niveaux d'alertes** dans Grafana :

### 1. 🔴 Surcharge Connexions (Critique)

| Paramètre | Valeur |
|-----------|--------|
| **Métrique** | `pg_stat_activity_count` |
| **Seuil** | `> 5` sessions actives |
| **Impact** | Risque de déni de service (DoS) si le pool de connexions sature |

#### Configuration de l'Alerte

**Étape 1 : Définir la Query Prometheus**

![Configuration Alerte - Query](images/Alerte_config_1.png)

La requête surveille le nombre de sessions actives sur `weather_db` :

```promql
sum(pg_stat_activity_count{datname="weather_db", state="active"})
```

**Étape 2 : Configurer les Expressions (Reduce + Threshold)**

![Configuration Alerte - Expressions](images/Alerte_config_2.png)

| Expression | Type | Configuration |
|------------|------|---------------|
| **B** | Reduce | Input: `A`, Function: `Last`, Mode: `Strict` |
| **C** | Threshold | Input: `B`, Condition: `IS ABOVE 5` |

**Résultat : Alerte en Action**

![Preview de l'alerte](images/Alerte_preview.png)

* **État Normal** : Badge vert "Normal" (sessions < 5)
* **État Firing** : Badge rouge quand le seuil est dépassé

La ligne rouge horizontale sur le graphique représente le seuil d'alerte configuré.

---

### 2. 🟠 Cache Hit Ratio Faible (Warning)

| Paramètre | Valeur |
|-----------|--------|
| **Métrique** | `pg_stat_database_blks_hit` / (`blks_hit` + `blks_read`) |
| **Seuil** | `< 90%` |
| **Impact** | La base lit trop souvent sur le disque (lent) au lieu de la RAM |

```promql
pg_stat_database_blks_hit{datname="weather_db"}
/ (pg_stat_database_blks_hit{datname="weather_db"} + pg_stat_database_blks_read{datname="weather_db"})
< 0.90
```

**Action recommandée** : Vérifier les index manquants ou augmenter `shared_buffers` dans la configuration PostgreSQL.

---

### 3. 🟡 Latence Anormale (Warning)

| Paramètre | Valeur |
|-----------|--------|
| **Métrique** | `pg_stat_activity_max_tx_duration` |
| **Seuil** | `> 1 seconde` |
| **Impact** | Une requête bloque ou une transaction est trop longue |

```promql
pg_stat_activity_max_tx_duration{datname="weather_db"} > 1
```

**Action recommandée** : Identifier la requête bloquante via `pg_stat_activity` et optimiser ou killer la session.

---

## 🏁 Bilan Jour 3

Ce TP a permis de connecter le monde du **développement** (Python/SQL) à celui des **opérations** (Monitoring). Nous avons démontré qu'optimiser une requête SQL ne se fait pas à l'aveugle, mais se **mesure** grâce à des métriques précises :

* **CPU Time** : Temps processeur consommé par les requêtes
* **Active Sessions** : Nombre de connexions en cours d'exécution
* **Transactions/sec** : Débit de la base de données
* **Alerting** : Détection automatique des anomalies

L'approche DevOps/SRE permet de **prouver par les données** l'impact d'une optimisation, plutôt que de se fier à des impressions subjectives.
