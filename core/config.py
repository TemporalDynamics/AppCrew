from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Backend
    firecrawl_api_key: str = ""
    linkedin_session_file: str = "data/linkedin_auth.json"

    # Search (Serper.dev — replaces Brave Search)
    serper_api_key: str = ""
    brave_search_api_key: str = ""  # legacy alias

    # LLM
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"

    # Dashboard
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8080
    dashboard_api_token: str = ""
    admin_access_code: str = ""

    # System
    orchestrator: str = "Manu"
    system_name: str = "Cerno"
    log_level: str = "info"

    # Playwright
    playwright_skip_browser_download: bool = False

    # WhatsApp
    whatsapp_business_number: str = ""

    # Email (Resend)
    resend_api_key: str = ""
    recruiter_email: str = ""

    # Apollo.io (enriquecimiento de emails)
    apollo_api_key: str = ""

    # GitHub API (sourcing)
    github_token: str = ""

    # Calendly
    calendly_link: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_bot_username: str = ""  # e.g. "TaloRecruitBot" (sin @)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def validate_critical(self) -> list[str]:
        missing = []
        if self.openrouter_api_key:
            pass
        if self.brave_search_api_key:
            pass
        return missing


settings = Settings()

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
