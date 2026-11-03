import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

class Config:
    PROJECT_NAME: str = "StockSathi"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Smart Retail Decision Engine for Shopkeepers"
    
    # Secret Key for JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "stocksathi-super-secret-key-2026-retail-engine")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # MongoDB Config
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "stocksathi_db")

    # Supabase Config
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # Server host & port
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Trial settings
    TRIAL_DURATION_DAYS: int = 3
    
    # Frontend directory
    FRONTEND_DIR: Path = BASE_DIR / "frontend"
    DATA_DIR: Path = BASE_DIR / "data" / "db"

config = Config()
