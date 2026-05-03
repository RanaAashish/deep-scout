from __future__ import annotations

import logging
from functools import lru_cache

from openai import AsyncOpenAI

from core.settings import Settings

logger = logging.getLogger(__name__)

_PROVIDER_CONFIG: dict[str, dict] = {
    "openai": {
        "base_url": None,  # use SDK default
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
    },
}


def _resolve_api_key(settings: Settings) -> str:
    """Return the API key for the configured provider."""
    provider = settings.llm_provider

    if provider == "openrouter":
        key = settings.openrouter_api_key
        if not key:
            raise ValueError(
                "OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter. "
                "Set it in your .env file."
            )
        return key

    if provider == "openai":
        key = settings.openai_api_key
        if not key:
            raise ValueError(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai. "
                "Set it in your .env file."
            )
        return key

    raise ValueError(
        f"Unknown LLM_PROVIDER={provider!r}. "
        f"Supported: {', '.join(_PROVIDER_CONFIG.keys())}"
    )


def _resolve_base_url(settings: Settings) -> str | None:
    """Return the base URL for the configured provider."""
    # Explicit override takes priority
    if settings.llm_base_url:
        return settings.llm_base_url

    provider = settings.llm_provider
    config = _PROVIDER_CONFIG.get(provider)
    if not config:
        raise ValueError(f"Unknown LLM_PROVIDER={provider!r}")

    return config["base_url"]


# ── Public API ───────────────────────────────────────────────

def get_chat_client(settings: Settings) -> AsyncOpenAI:
    """
    Returns an AsyncOpenAI client configured for the active provider.

    Used by: planner, critic, draft_generator, synthesizer, brief_writer.
    """
    api_key = _resolve_api_key(settings)
    base_url = _resolve_base_url(settings)

    kwargs: dict = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url

    logger.debug("Creating LLM client: provider=%s, base_url=%s", settings.llm_provider, base_url)
    return AsyncOpenAI(**kwargs)


def get_agent_model(settings: Settings, *, writer: bool = False):
    """
    Returns a model instance for the openai-agents SDK Agent().

    If provider is 'openai', returns a plain model string (native support).
    For all other providers, returns an OpenAIChatCompletionsModel wrapping
    a custom AsyncOpenAI client.

    Args:
        writer: If True, use the writer model name instead of the default model.
    """
    model_name = settings.openai_writer_model if writer else settings.openai_model

    if settings.llm_provider == "openai" and not settings.llm_base_url:
        # Native OpenAI — just return the model string
        return model_name

    # Non-OpenAI provider — wrap in OpenAIChatCompletionsModel
    from agents import OpenAIChatCompletionsModel

    client = get_chat_client(settings)
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)
