"""
Centralized Configuration Management

All paths, API keys, and settings are managed here using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Centralized application settings"""

    # Paths - automatically computed relative to project root
    project_root: Path = Path(__file__).parent.parent.parent
    package_dir: Path = Path(__file__).parent
    data_dir: Path = project_root / "data"

    # Data pipeline paths
    bronze_dir: Path = data_dir / "bronze"
    silver_db_path: Path = data_dir / "duck_db" / "silver" / "cricket_stats.duckdb"
    chroma_db_path: Path = data_dir / "chroma_db"

    # Config paths (now inside package)
    config_dir: Path = package_dir / "config"
    cricket_news_config: Path = config_dir / "cricket_news.yaml"
    logging_config: Path = config_dir / "logging.yaml"

    # API Keys (loaded from .env) - match env var names exactly
    openai_api: str = ""      # Loaded from OPENAI_API
    gnews_api_key: str = ""   # Loaded from GNEWS_API_KEY

    # Model Settings
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0

    # Database Settings
    chroma_collection_name: str = "cricket_news"
    max_sql_result_rows: int = 100

    # News Settings
    max_news_articles: int = 10
    news_search_top_k: int = 5

    # Property to provide clean API access
    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key (alias for openai_api)"""
        return self.openai_api

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # Ignore extra fields from .env
    }


# Singleton instance - import this in your modules
settings = Settings()
