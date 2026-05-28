from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Backend
    firecrawl_api_key: str = ""
    linkedin_session_file: str = "data/linkedin_auth.json"

    # Search
    brave_search_api_key: str = ""

    # LLM
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"

    # Dashboard
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8080
    dashboard_api_token: str = ""

    # System
    orchestrator: str = "Manu"
    system_name: str = "Cerno"
    log_level: str = "info"

    # Playwright
    playwright_skip_browser_download: bool = False

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
