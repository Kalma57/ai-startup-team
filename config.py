"""Configuration from environment variables / .env (never hard-code keys or models)."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

PLACEHOLDER_KEY = "paste-your-key-here"


class ConfigError(Exception):
    """Raised when required configuration is missing."""


@dataclass(frozen=True)
class Settings:
    api_key: str
    research_model: str   # used for Google Search calls
    agent_model: str      # used for structuring / all other agents

    def __repr__(self) -> str:  # never leak the key in logs
        return (f"Settings(api_key=***, research_model={self.research_model!r}, "
                f"agent_model={self.agent_model!r})")


def load_settings() -> Settings:
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == PLACEHOLDER_KEY:
        raise ConfigError(
            "GEMINI_API_KEY is missing. Copy .env.example to .env and paste your key "
            "(free key: https://aistudio.google.com/apikey)."
        )
    research_model = os.getenv("RESEARCH_MODEL", "").strip()
    agent_model = os.getenv("AGENT_MODEL", "").strip()
    if not research_model or not agent_model:
        raise ConfigError("RESEARCH_MODEL and AGENT_MODEL must be set in .env (see .env.example).")
    return Settings(api_key=key, research_model=research_model, agent_model=agent_model)
