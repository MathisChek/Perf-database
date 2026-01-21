# ⚡ Benchmark SQL vs NoSQL : Pokémon Database

Ce projet a pour but de comparer les performances entre une base relationnelle (**PostgreSQL**) et une base orientée documents (**MongoDB**) sur un volume de données significatif (**500 000 enregistrements**).

Le scénario simule les logs d'un jeu type "Pokémon GO" : des captures de Pokémon effectuées par des dresseurs à des coordonnées GPS variées, avec différentes météos.

---

## 🚀 Guide de Démarrage

Voici la procédure pas-à-pas pour installer le projet, générer les données et lancer les tests de performance.

### 1. Pré-requis

* **Docker** & Docker Compose
* **Python 3.8+**
* Un client SQL (ex: Beekeeper Studio) et un client Mongo (MongoDB Compass)

### 2. Installation

Clonez le dépôt et installez les dépendances Python nécessaires :

```bash
git clone https://github.com/votre-repo/perf-database.git
cd perf-database
pip install psycopg2-binary pymongo python-dotenv faker requests terminaltables
```

### 3. Configuration (.env)

Créez un fichier `.env` à la racine du projet.

> **Attention** : Pour éviter les erreurs de connexion Docker en local, utilisez l'IP `127.0.0.1` et forcez la source d'authentification pour MongoDB.

```ini
# --- PostgreSQL Local ---
POSTGRES_USER=etudiant
POSTGRES_PASSWORD=password
POSTGRES_DB=pokedb
POSTGRES_PORT=5433

# --- MongoDB Local ---
# Note : on utilise 127.0.0.1 et directConnection pour éviter les échecs de résolution DNS
MONGO_URI="mongodb://etudiant:password@127.0.0.1:27017/?authSource=admin&directConnection=true"
```

### 4. Lancement de l'Infrastructure

Démarrez les conteneurs (Postgres et Mongo) :

```bash
docker-compose up -d
```

### 5. Ingestion des Données (Génération)

Avant de lancer le script Python, vous devez créer la base de données SQL manuellement (le script ne peut pas créer la base s'il ne peut pas s'y connecter).

1. Connectez-vous à PostgreSQL (`localhost:5433`, user: `etudiant`, pass: `password`)
2. Exécutez la commande SQL : `CREATE DATABASE pokedb;`
3. Lancez le script d'ingestion :

```bash
python3 Day2/ingest.py
```

Ce script télécharge les infos réelles depuis l'API Pokémon, génère 500 000 captures aléatoires et peuple les deux bases simultanément pour assurer une égalité parfaite des données.

### 6. Lancer le Benchmark

Pour exécuter les 5 requêtes de test et voir les temps de réponse :

```bash
python3 benchmark.py
```

---

## 📂 Modélisation des Données

### 🐘 PostgreSQL : Modèle en Étoile (Normalisé)

Pour éviter la redondance, nous utilisons une structure relationnelle classique :

* **fact_captures** (500k lignes) : Contient l'événement (Date, Lat, Long, Météo) et une Clé Étrangère vers le Pokémon.
* **dim_pokemons** (151 lignes) : Contient les infos fixes (Nom, Type, Stats).

**Conséquence** : Jointure (`JOIN`) obligatoire pour récupérer le nom du Pokémon.

### 🍃 MongoDB : Modèle Imbriqué (Dénormalisé)

Nous privilégions la lecture rapide :

* **Collection captures** (500k documents) : Chaque document contient l'événement ET la fiche complète du Pokémon capturé (sous-objet JSON).

**Conséquence** : Pas de jointure, mais forte duplication de données (le mot "Pikachu" est stocké des milliers de fois).

---

## 📊 Phase 1 : Analyse du Stockage

| Critère | PostgreSQL | MongoDB (WiredTiger) |
|---------|------------|----------------------|
| Nombre de lignes | 500 000 | 500 000 |
| Taille Disque | 50 MB | 43.1 MB 🏆 |

**Observation** : Contre toute attente, MongoDB est plus léger.

**Explication** : Bien que MongoDB duplique les données, son moteur de stockage (WiredTiger) utilise par défaut la compression Snappy, très efficace sur les répétitions de texte dans les documents JSON. PostgreSQL stocke les données brutes sans compression par défaut.

---

## 🏎️ Phase 2 : Performance sans Index (Brute Force)

Dans cette phase, aucun index n'est créé. Les moteurs doivent scanner l'intégralité du disque ("Full Scan") pour trouver les réponses.

| Scénario | PostgreSQL (ms) | MongoDB (ms) | Vainqueur |
|----------|-----------------|--------------|-----------|
| 1. Recherche Exacte (Pikachu) | 35.64 ms | 245 ms | 🐘 SQL |
| 2. Intervalle (Lat > 45) | 86.52 ms | 258 ms | 🐘 SQL |
| 3. Agrégation (Count Météo) | 50.69 ms | 498 ms | 🐘 SQL |
| 4. Complexe (Electric + Rainy) | 36.35 ms | 271 ms | 🐘 SQL |
| 5. Agrégation Lourde (Avg HP) | 84.15 ms | 724 ms | 🐘 SQL |

**Analyse** : Sur un scan complet, PostgreSQL écrase MongoDB. Lire des lignes SQL simples ("tuples") est beaucoup moins coûteux pour le CPU que de parser 500 000 documents JSON imbriqués.

### 🔬 Comprendre les Types de Scan

Pour expliquer cet écart de performance, il faut comprendre comment chaque moteur parcourt les données sans index.

#### PostgreSQL : Sequential Scan (Seq Scan)

```sql
EXPLAIN ANALYZE SELECT * FROM fact_captures WHERE pokemon_id = 25;
-- Seq Scan on fact_captures  (cost=0.00..12847.00 rows=3289 width=36)
--   Filter: (pokemon_id = 25)
```

PostgreSQL effectue un **Sequential Scan** : il lit les pages disque de manière linéaire, tuple par tuple. Chaque ligne est un enregistrement binaire à taille fixe avec des colonnes typées. Le moteur n'a qu'à :

1. Lire le bloc disque (8 Ko par défaut)
2. Extraire directement les valeurs des colonnes via leur offset mémoire
3. Appliquer le filtre sur une donnée déjà typée (integer, float, varchar...)

Le coût CPU est minimal car il n'y a **aucun parsing** : les données sont stockées dans un format binaire optimisé, prêt à être comparé.

#### MongoDB : Collection Scan (COLLSCAN)

```javascript
db.captures.find({ "pokemon.name": "Pikachu" }).explain("executionStats")
// "stage": "COLLSCAN"
// "docsExamined": 500000
```

MongoDB effectue un **Collection Scan** : il parcourt tous les documents de la collection. Mais contrairement à SQL, chaque document est un objet BSON (Binary JSON) de taille variable avec une structure flexible. Pour chaque document, le moteur doit :

1. Lire le document BSON depuis le disque
2. **Parser la structure** pour localiser le champ recherché (ex: `pokemon.name`)
3. Naviguer dans l'arborescence imbriquée (ici, descendre dans le sous-objet `pokemon`)
4. Décoder la valeur et effectuer la comparaison

Ce parsing dynamique, répété 500 000 fois, génère un **overhead CPU significatif**.

#### Comparaison visuelle

| Aspect | PostgreSQL (Seq Scan) | MongoDB (COLLSCAN) |
|--------|----------------------|---------------------|
| Format de stockage | Tuples binaires à colonnes fixes | Documents BSON de taille variable |
| Accès aux champs | Offset direct en mémoire | Parsing + navigation dans l'arbre |
| Coût par enregistrement | ~1 opération (lecture) | ~3-5 opérations (lecture + parsing + navigation) |
| Adapté pour | Données tabulaires homogènes | Données flexibles et imbriquées |

#### Pourquoi l'écart se creuse sur les agrégations ?

Sur les requêtes 3 et 5 (COUNT, AVG), PostgreSQL utilise des optimisations supplémentaires :

* **Vectorisation** : traitement par lots de valeurs plutôt qu'une par une
* **Types natifs** : les calculs sur `INTEGER` ou `FLOAT` sont des opérations CPU primitives
* **Pas de désérialisation** : les valeurs numériques sont directement exploitables

MongoDB, avec son Aggregation Pipeline, doit désérialiser chaque valeur BSON avant de l'accumuler, ce qui multiplie le coût par document.

---

## 🔧 Phase 3 : Performance AVEC Index (Optimisé)

Nous avons créé des index B-Tree sur Postgres et des index spécifiques sur les champs imbriqués dans Mongo.

### Index créés

```sql
-- PostgreSQL
CREATE INDEX idx_pokemon_id ON fact_captures(pokemon_id);
CREATE INDEX idx_latitude ON fact_captures(latitude);
CREATE INDEX idx_weather ON fact_captures(weather);
```

```javascript
// MongoDB
db.captures.createIndex({ "pokemon.name": 1 })
db.captures.createIndex({ "latitude": 1 })
db.captures.createIndex({ "weather": 1 })
```

### Résultats finaux

| Scénario | PostgreSQL (Indexé) | MongoDB (Indexé) | Vainqueur |
|----------|---------------------|------------------|-----------|
| 1. Recherche Exacte (Pikachu) | 14.51 ms | 8 ms ⚡ | 🍃 MONGO |
| 2. Intervalle (Lat > 45) | 75.43 ms | 447 ms | 🐘 SQL |
| 3. Agrégation (Count Météo) | 61.08 ms | 546 ms | 🐘 SQL |
| 4. Complexe (Electric + Rainy) | 50.44 ms | 20 ms ⚡ | 🍃 MONGO |
| 5. Agrégation Lourde (Avg HP) | 112.05 ms | 752 ms | 🐘 SQL |

### 🔬 Comprendre les Types de Scan avec Index

#### PostgreSQL : Index Scan + Heap Fetch

```sql
EXPLAIN ANALYZE SELECT * FROM fact_captures fc
JOIN dim_pokemons dp ON fc.pokemon_id = dp.id
WHERE dp.name = 'Pikachu';
-- Index Scan using idx_pokemon_id on fact_captures
-- Nested Loop Join with dim_pokemons
```

Avec un index, PostgreSQL effectue un **Index Scan** en deux temps :

1. **Parcours de l'index B-Tree** : localise les `pokemon_id` correspondants (très rapide, O(log n))
2. **Heap Fetch** : pour chaque entrée trouvée, retourne dans la table principale (le "heap") récupérer la ligne complète
3. **Nested Loop Join** : pour chaque ligne, fait une jointure avec `dim_pokemons` pour récupérer le nom

C'est cette étape de jointure qui pénalise PostgreSQL sur la requête 1.

#### MongoDB : Index Scan + Document Direct

```javascript
db.captures.find({ "pokemon.name": "Pikachu" }).explain("executionStats")
// "stage": "IXSCAN" → "stage": "FETCH"
// "keysExamined": 3289, "docsExamined": 3289
```

MongoDB avec index effectue :

1. **IXSCAN** : parcours de l'index B-Tree sur `pokemon.name`
2. **FETCH** : récupération directe du document complet

**Pas de jointure nécessaire** : le document contient déjà toutes les informations (nom, stats, date de capture...). C'est le bénéfice direct du modèle dénormalisé.

#### Pourquoi MongoDB gagne sur la recherche unitaire ?

| Étape | PostgreSQL | MongoDB |
|-------|-----------|---------|
| 1. Traversée index | ✅ O(log n) | ✅ O(log n) |
| 2. Récupération données | Heap fetch (table faits) | Document fetch (complet) |
| 3. Jointure | ⚠️ Lookup vers dim_pokemons | ❌ Non nécessaire |
| 4. Assemblage résultat | Fusion des deux tables | Déjà prêt |

Le modèle imbriqué de MongoDB élimine complètement l'étape de jointure, ce qui fait la différence sur les lectures unitaires.

#### Pourquoi PostgreSQL domine toujours sur les agrégations ?

Même avec index, les requêtes analytiques (COUNT, AVG, filtres sur plages) favorisent PostgreSQL :

* **Index-Only Scan** : PostgreSQL peut parfois répondre uniquement depuis l'index sans toucher au heap
* **Bitmap Index Scan** : pour les grandes plages, PostgreSQL construit un bitmap en mémoire puis fait un seul passage sur le disque
* **Parallel Seq Scan** : PostgreSQL peut paralléliser les agrégations sur plusieurs CPU cores

MongoDB, même indexé, doit toujours fetch et parser les documents BSON pour extraire les valeurs à agréger.

---

## 🕵️‍♂️ Analyse et Conclusion

### Le K.O. technique de MongoDB (Recherches ciblées)

Sur les requêtes 1 ("Trouver Pikachu") et 4 ("Electric + Rainy"), MongoDB est respectivement **1.8x** et **2.5x plus rapide** que SQL.

**Pourquoi ?** Ces deux requêtes partagent un point commun : elles filtrent sur des champs **contenus dans le document** (`pokemon_details.name`, `pokemon_details.type`, `weather`). Une fois l'index trouvé, Mongo lit le document et a déjà toutes les infos nécessaires. PostgreSQL, même indexé, doit faire une étape supplémentaire : la **Jointure** entre la table des faits et la dimension pour récupérer le type du Pokémon. C'est là que le NoSQL brille.

### La domination de SQL (Analytique)

Dès qu'il s'agit de compter, filtrer sur des plages ou faire des moyennes (Requêtes 2, 3, 5), PostgreSQL reste supérieur. Son moteur est optimisé pour les calculs mathématiques sur des colonnes typées, là où l'Aggregation Pipeline de Mongo demande plus de ressources mémoire.

---

## 🏆 Verdict

* **Utilisez MongoDB** pour des accès directs à des objets complets (Profil utilisateur, Catalogue produit, Fiche détaillée).
* **Utilisez PostgreSQL** pour des requêtes analytiques, des statistiques et des relations complexes.
