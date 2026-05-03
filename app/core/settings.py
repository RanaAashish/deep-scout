from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Provider selection ──────────────────────────────────
    llm_provider: str = Field(default="openrouter", validation_alias="LLM_PROVIDER")
    llm_base_url: str = Field(default="", validation_alias="LLM_BASE_URL")

    # ── API keys ─────────────────────────────────────────────
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openrouter_api_key: str = Field(default="", validation_alias="OPENROUTER_API_KEY")

    tavily_api_key: str | None = Field(default=None, validation_alias="TAVILY_API_KEY")
    serper_api_key: str | None = Field(default=None, validation_alias="SERPER_API_KEY")

    # ── Model names (used by whatever provider is active) ────
    openai_model: str = Field(default="openai/gpt-4o-mini", validation_alias="OPENAI_MODEL")
    openai_writer_model: str = Field(
        default="openai/gpt-4o-mini", validation_alias="OPENAI_WRITER_MODEL"
    )

    prompt_version: str = Field(default="v1", validation_alias="SHADOW_WRITER_PROMPT_VERSION")

    artifacts_dir: Path = Field(
        default_factory=lambda: Path("artifacts"),
        validation_alias="SHADOW_WRITER_ARTIFACTS_DIR",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
