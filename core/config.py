import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# --- Database ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set or .env file not found.")

# --- Elasticsearch ---
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_INDEX = os.getenv("ES_INDEX", "codesearch_index")
ES_API_KEY = os.getenv("ES_API_KEY")

if not ES_API_KEY:
    raise ValueError("ES_API_KEY environment variable not set or .env file not found.")

# --- Model ---
MODEL_NAME = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")

# --- FeatherlessAI ---
FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")
FEATHERLESS_BASE_URL = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1")
FEATHERLESS_VISION_MODEL = os.getenv("FEATHERLESS_VISION_MODEL", "google/gemma-3-27b-it")

# --- Auth ---
# This is for JWT, which we might use later for a web UI
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_that_should_be_in_env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
