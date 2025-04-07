from pydantic_settings import BaseSettings
from typing import List, Optional


class ApiSettings(BaseSettings):
    """API Settings loaded from environment variables"""

    # API Settings
    title: str = "Financial Modeling API"
    version: str = "1.0.0"
    docs_enabled: bool = True
    api_key: str = "test-api-key"
    
    # CORS Settings
    cors_origin_list: List[str] = ["*"]
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Default Provider Settings
    default_provider: str = "formation"
    default_model_id: Optional[str] = None
    default_temperature: float = 0.1
    
    # Directory Settings
    uploads_dir: str = "uploads"

    class Config:
        env_prefix = "FAMA_"
        case_sensitive = False


# Create API settings instance
api_settings = ApiSettings() 