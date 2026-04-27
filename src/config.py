"""Environment configuration for the PoC."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """App settings loaded from environment variables."""

    llm_provider: str = "mock"
    # Optional on purpose: this PoC runs without paid APIs.
    openai_api_key: str | None = None


def load_settings() -> Settings:
    """Load environment variables and return typed settings."""
    load_dotenv()
    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "mock"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
