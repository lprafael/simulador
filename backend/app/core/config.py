from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Base de datos
    DATABASE_URL: str = "postgresql://simulador:simulador123@db:5432/simulador"
    
    # Bases de datos externas
    CID_DB_URL: str = ""
    MONITOREO_DB_URL: str = ""
    BILLETAJE_DB_URL: str = ""
    
    # Waze for Cities
    WAZE_CCP_FEED_URL: str = "https://feed.waze.com/partner-feed/asuncion-gran-asuncion"
    WAZE_API_KEY: str = ""
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production-32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # Simulación
    SIM_DEFAULT_HEADWAY: float = 8.0       # minutos
    SIM_DEFAULT_VELOCIDAD: float = 25.0    # km/h
    SIM_BUNCHING_UMBRAL: float = 0.5       # ratio headway_real / headway_prog
    SIM_TIEMPO_PARADA_BASE: float = 0.5    # minutos
    SIM_TIEMPO_POR_PASAJERO: float = 0.05  # minutos por pasajero
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
