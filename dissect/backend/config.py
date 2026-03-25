import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME = "DISSECT"

    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    REPO_DIR = os.path.join(DATA_DIR, "repos")
    CACHE_DIR = os.path.join(DATA_DIR, "cache")

    # LLM Config
    USE_LOCAL_LLM = True
    OLLAMA_MODEL = "llama3"

    # Security
    ALLOWED_DOMAINS = ["github.com"]

    # ML
    MODEL_PATH = os.path.join(DATA_DIR, "models", "vulnerability_xgboost.json")

settings = Settings()