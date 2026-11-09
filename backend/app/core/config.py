from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "NetScope"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATA_DIR / 'netscope.db'}"
    SYNC_DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'netscope.db'}"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    TELEMETRY_INTERVAL_SECONDS: float = 1.5
    MAX_CONCURRENT_PORT_SCANS: int = 50

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()
