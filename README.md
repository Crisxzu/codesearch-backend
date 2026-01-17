# CodeSearch Backend

> API REST pour la recherche sémantique de code, documents et images avec embeddings vectoriels.

## 📋 Vue d'ensemble

CodeSearch Backend est une API FastAPI qui permet d'indexer et de rechercher du code source, des documents (PDF, DOCX, Markdown) et des images en utilisant des embeddings vectoriels et Elasticsearch. Le système utilise des transformers pour convertir le texte en vecteurs, et un modèle de vision IA pour analyser les images.

### Fonctionnalités principales

- ✅ **Indexation multimodale** : Code, documents (PDF, DOCX, MD), images
- ✅ **Recherche sémantique** : Recherche par similarité vectorielle avec seuil de pertinence
- ✅ **Parsing intelligent** : Extraction de fonctions/classes avec Tree-sitter
- ✅ **Vision AI** : Description automatique d'images via FeatherlessAI
- ✅ **Authentification** : API keys avec PostgreSQL
- ✅ **Chunking** : Découpage automatique des fichiers volumineux

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
│  (CLI/Web)  │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────────────────────────────┐
│         FastAPI Backend             │
│  ┌─────────────────────────────┐   │
│  │  API Layer (api/)           │   │
│  │  - auth.py                  │   │
│  │  - mgrep.py                 │   │
│  │  - schemas.py               │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │  Services (services/)       │   │
│  │  - indexing_service.py      │   │
│  │  - search_service.py        │   │
│  │  - vision_service.py        │   │
│  │  - document_service.py      │   │
│  │  - es_manager.py            │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │  Auth (auth/)               │   │
│  │  - api_key.py               │   │
│  │  - security.py              │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
       │              │
       ▼              ▼
┌─────────────┐  ┌──────────────┐
│ PostgreSQL  │  │ Elasticsearch│
│  (Auth)     │  │  (Vectors)   │
└─────────────┘  └──────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ SentenceTransf. │
              │ all-MiniLM-L6-v2│
              │   (384 dims)    │
              └─────────────────┘
```

## 🚀 Installation

### Prérequis

- **Python 3.12+**
- **PostgreSQL** (pour l'authentification)
- **Elasticsearch 7.x+** (pour le stockage des vecteurs)
- **Compte FeatherlessAI** (optionnel, pour les images)

### 1. Cloner le repository

```bash
git clone https://github.com/your-username/codesearch-backend.git
cd codesearch-backend
```

### 2. Créer un environnement virtuel

```bash
python -m venv .venv
source .venv/bin/activate  # Sur macOS/Linux
# .venv\Scripts\activate   # Sur Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configuration

Créez un fichier `.env` à la racine du projet :

```env
# PostgreSQL (authentification)
DATABASE_URL=postgresql://user:password@localhost:5432/codesearch

# Elasticsearch (stockage des vecteurs)
ES_HOST=localhost
ES_PORT=9200
ES_USER=elastic
ES_PASSWORD=your_password

# FeatherlessAI (vision pour images - optionnel)
FEATHERLESS_API_KEY=your_api_key
FEATHERLESS_VISION_MODEL=llama-3.2-11b-vision-instruct

# JWT Secret (pour l'authentification)
SECRET_KEY=your_very_secret_key_here

# CORS (optionnel)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 5. Initialiser la base de données

```bash
# Créer les tables PostgreSQL
python -c "from backend.db.database import init_db; init_db()"

# Créer l'index Elasticsearch
python -c "from backend.services.es_manager import ElasticsearchManager; ElasticsearchManager().create_index()"
```

### 6. Lancer le serveur

```bash
uvicorn backend.main:app --reload
```

L'API sera accessible sur `http://localhost:8000`

## 📚 API Endpoints

### Documentation interactive

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

### Authentification

#### `POST /api/auth/request-code`

Demander un code de vérification par email.

```json
{
  "email": "user@example.com"
}
```

#### `POST /api/auth/verify-code`

Vérifier le code et obtenir une API key.

```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response :**
```json
{
  "api_key": "csk_abc123...",
  "user_id": "user-uuid"
}
```

### Indexation

#### `POST /api/index`

Indexer du code source (JSON).

**Headers :**
```
X-API-Key: csk_abc123...
```

**Body :**
```json
{
  "file_path": "src/utils/helpers.py",
  "content": "def calculate_sum(a, b):\n    return a + b",
  "project_name": "my-project"
}
```

#### `POST /api/index/file`

Indexer un fichier (multipart/form-data) - images, PDF, DOCX.

**Headers :**
```
X-API-Key: csk_abc123...
Content-Type: multipart/form-data
```

**Form data :**
- `file`: fichier binaire (image, PDF, DOCX)
- `file_path`: chemin du fichier
- `project_name`: nom du projet

### Recherche

#### `GET /api/search`

Recherche sémantique dans le code indexé.

**Headers :**
```
X-API-Key: csk_abc123...
```

**Query params :**
- `q` (required): requête de recherche
- `project_name` (optional): filtrer par projet
- `top_k` (optional): nombre de résultats (défaut: 5)

**Response :**
```json
{
  "results": [
    {
      "file_path": "src/utils/helpers.py",
      "content": "def calculate_sum(a, b):\n    return a + b",
      "similarity_score": 0.85,
      "project_name": "my-project",
      "content_type": "code",
      "start_line": 1,
      "end_line": 3
    }
  ],
  "query": "calculate the sum of two numbers",
  "count": 1
}
```

## 🔧 Structure du projet

```
backend/
├── __init__.py
├── main.py                    # Point d'entrée FastAPI
├── api/
│   ├── __init__.py
│   ├── auth.py               # Endpoints d'authentification
│   ├── mgrep.py              # Endpoints indexation/recherche
│   ├── schemas.py            # Schémas Pydantic
│   └── dependencies.py       # Dépendances FastAPI
├── auth/
│   ├── __init__.py
│   ├── api_key.py            # Génération API keys
│   └── security.py           # Validation API keys
├── core/
│   ├── __init__.py
│   └── config.py             # Configuration (env vars)
├── db/
│   ├── __init__.py
│   ├── database.py           # PostgreSQL connection
│   └── models.py             # Modèles SQLAlchemy
└── services/
    ├── __init__.py
    ├── es_manager.py         # Gestion Elasticsearch
    ├── indexing_service.py   # Indexation multimodale
    ├── search_service.py     # Recherche sémantique
    ├── vision_service.py     # FeatherlessAI vision
    └── document_service.py   # Extraction PDF/DOCX/MD
```

## 🧠 Concepts techniques

### Embeddings vectoriels

Les embeddings transforment le texte en vecteurs numériques (384 dimensions) qui capturent le sens sémantique. Le modèle utilisé est **all-MiniLM-L6-v2** de SentenceTransformers.

**Exemple :**
```python
"calculate sum" → [0.12, -0.34, 0.56, ..., 0.89]  # 384 dimensions
"add numbers"   → [0.15, -0.31, 0.52, ..., 0.91]  # Vecteur similaire
```

La similarité est mesurée avec le **cosine similarity** (1 = identique, -1 = opposé).

### Chunking

Les fichiers trop longs sont découpés en chunks de **MAX_CHUNK_SIZE = 500 caractères** pour :
- Améliorer la précision de la recherche
- Réduire le bruit (éviter de mélanger plusieurs concepts)
- Respecter les limites des modèles

**Limitations actuelles :**
- Le chunking peut couper au milieu d'une fonction
- Solution future : parser l'AST et chunker par fonction/classe

### Vision AI pour images

Les images sont converties en descriptions textuelles via le modèle **llama-3.2-11b-vision-instruct** :

1. Image uploadée → optimisée (max 800x800px)
2. Envoyée à FeatherlessAI
3. Modèle génère description
4. Description → embedding vectoriel
5. Stocké dans Elasticsearch

**Coût approximatif :** ~$0.001-0.005 par image

### Retry logic

Les appels à FeatherlessAI utilisent un système de retry avec backoff exponentiel :
- 3 tentatives maximum
- Délai : 2s, 4s, 8s
- Erreurs retryables : 503, 429, server_error

## 🛠️ Développement

### Lancer en mode dev

```bash
uvicorn backend.main:app --reload --log-level debug
```

### Recréer l'index Elasticsearch

Si vous changez le mapping Elasticsearch :

```bash
python -c "from backend.services.es_manager import ElasticsearchManager; ElasticsearchManager().recreate_index()"
```

### Tests

```bash
# Installer pytest
pip install pytest pytest-asyncio

# Lancer les tests
pytest tests/
```

### Variables d'environnement importantes

| Variable | Description | Défaut |
|----------|-------------|--------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `ES_HOST` | Elasticsearch host | `localhost` |
| `ES_PORT` | Elasticsearch port | `9200` |
| `FEATHERLESS_API_KEY` | API key FeatherlessAI | - |
| `MAX_CHUNK_SIZE` | Taille max d'un chunk (chars) | `500` |
| `MIN_SIMILARITY_THRESHOLD` | Seuil min de similarité | `0.1` |
| `SECRET_KEY` | Secret pour JWT | - |

## ⚠️ Limitations connues

1. **Chunking non optimal** : Peut couper au milieu d'une fonction
2. **Scalabilité** : Fetch tous les documents puis tri en Python (ne scale pas au-delà de ~1000 fichiers)
3. **Pas de cache** : Les descriptions d'images ne sont pas mises en cache
4. **Suppression manuelle** : Les fichiers supprimés ne sont pas automatiquement retirés de l'index
5. **Seuil fixe** : Le seuil de similarité (0.1) n'est pas configurable via l'API

## 📊 Performance

- **Indexation** : ~100-200ms par fichier (code)
- **Recherche** : ~50-100ms pour 1000 documents
- **Vision AI** : ~2-5s par image

## 🔐 Sécurité

- API keys stockées hashées (SHA-256) dans PostgreSQL
- Validation des API keys sur tous les endpoints sensibles
- CORS configuré via `ALLOWED_ORIGINS`
- Pas de rate limiting (TODO)

## 📝 Logs

Les logs sont configurés avec le niveau `INFO` par défaut :

```python
import logging
logging.basicConfig(level=logging.INFO)
```

Pour plus de verbosité :
```bash
uvicorn backend.main:app --reload --log-level debug
```

## 🐛 Dépannage

### Elasticsearch connection refused

Vérifiez qu'Elasticsearch est démarré :
```bash
curl http://localhost:9200
```

### PostgreSQL connection error

Vérifiez votre `DATABASE_URL` et que PostgreSQL est accessible :
```bash
psql postgresql://user:password@localhost:5432/codesearch
```

### FeatherlessAI 503 errors

Le service peut être temporairement surchargé. Le retry logic (3 tentatives) devrait gérer ça automatiquement.

### Pas de résultats de recherche

1. Vérifiez que des documents sont indexés : `curl http://localhost:9200/codesearch/_count`
2. Vérifiez que le `user_id` correspond
3. Abaissez le seuil de similarité temporairement

## 📄 Licence

MIT

## 🔗 Liens

- [CLI CodeSearch](https://github.com/your-username/codesearch-cli)
- [Documentation Elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [SentenceTransformers](https://www.sbert.net/)
- [FeatherlessAI](https://featherless.ai/)

## 👤 Auteur

Chris Kouassi
