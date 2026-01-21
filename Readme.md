# 🚀 Workshop : Performance des Bases de Données & Observabilité

Ce dépôt contient les livrables d'un workshop intensif de **3 jours** consacré à l'optimisation, la comparaison et le monitoring des bases de données modernes.

L'objectif était de passer d'une approche "code-first" à une approche **"data-centric"**, en comprenant comment les moteurs de bases de données fonctionnent sous le capot (Index, Buffers, Scan, Sharding).

---

## 📂 Structure du Projet

Le travail est réparti en 3 modules distincts, chacun isolable via Docker :

```
.
├── Day1/                    # 📊 Audit & Optimisation SQL
│   ├── Scénario : Plateforme E-learning (200k étudiants, 5M logs)
│   └── Objectif : Analyser les plans d'exécution (EXPLAIN) et indexer.
│
├── Day2/                    # ⚔️ Benchmark SQL vs NoSQL
│   ├── Scénario : Big Data Pokémon (500k captures, API réelle)
│   └── Objectif : Comparer PostgreSQL vs MongoDB (Partitionnement, Vues Matérialisées).
│
└── Day3/                    # 📡 Monitoring & SRE
    ├── Scénario : Ingestion Météo Temps Réel (OpenWeatherMap)
    └── Objectif : Infrastructure Prometheus/Grafana et Alerting en production.
```

---

## 📅 Détail des Modules

### Jour 1 : Audit de Sécurité & Indexation B-Tree

**Contexte** : Une base de données d'école en ligne souffre de lenteurs critiques.

**Réalisations** :
* Génération de données massives (5M lignes)
* Audit des requêtes lentes via `EXPLAIN (ANALYZE, BUFFERS)`
* Mise en place d'une stratégie d'indexation (Composite, Covering Index)

**Apprentissage clé** : Le paradoxe de la régression — pourquoi un index peut parfois ralentir une requête sans `LIMIT`.

---

### Jour 2 : PostgreSQL vs MongoDB

**Contexte** : Stockage de logs de jeux (Pokémon) avec des données géospatiales et JSON imbriqué.

**Réalisations** :
* Script d'ingestion Python (ETL) depuis l'API PokéAPI
* Benchmark de performance : `Seq Scan` vs `COLLSCAN`
* Optimisation avancée : Partitionnement Temporel (SQL) et Indexation JSON (Mongo)

**Apprentissage clé** : MongoDB excelle sur la lecture unitaire (Document), PostgreSQL domine sur l'analytique (Agrégations).

---

### Jour 3 : Monitoring Industriel & Alerting

**Contexte** : Surveillance d'une application météo "Live" en production.

**Réalisations** :
* Déploiement d'une stack SRE : Postgres Exporter + Prometheus + Grafana
* Stress Test : Simulation de 10 utilisateurs concurrents
* Preuve visuelle de l'optimisation (Chute de la charge CPU et des sessions actives)
* Configuration d'alertes (Surcharge connexions, Cache Hit Ratio)

**Apprentissage clé** : On n'optimise pas à l'aveugle, on optimise ce qu'on mesure.

---

## 🛠️ Stack Technique Globale

| Catégorie | Technologies |
|-----------|--------------|
| **Langages** | Python 3.10, SQL, JavaScript (Mongosh) |
| **Bases de données** | PostgreSQL 15, MongoDB 6 |
| **Outils SRE** | Prometheus, Grafana, Docker & Docker Compose |
| **Clients** | Beekeeper Studio, MongoDB Compass |

---

## 🚀 Installation Générale

Chaque dossier (`Day1`, `Day2`, `Day3`) est indépendant et possède son propre `docker-compose.yml`.

Pour lancer un module :

```bash
# Exemple pour le Jour 3
cd Day3
docker-compose up -d
pip install -r requirements.txt
python3 scripts/weather_collector.py
```

---

> Projet réalisé dans le cadre du module "Performance des SGBD".
