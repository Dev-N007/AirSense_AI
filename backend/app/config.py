import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "AirSense AI Backend"
    API_V1_STR: str = "/api"
    
    # DB URL - Fallback to SQLite locally, supports Supabase Postgres URL
    DATABASE_URL: str = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL") or "sqlite:///./airsense.db"
    
    # Gemini API Key
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY") or ""
    
    # Model Directories
    MODEL_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trained_models")
    
    # Port & Host
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT") or 8000)

settings = Settings()
