from flask import current_app

from .base import AIConfigurationError, AIProvider
from .openai import OpenAIProvider


def get_ai_provider() -> AIProvider:
    injected = current_app.config.get("AI_PROVIDER_INSTANCE")
    if injected is not None:
        return injected

    provider_name = str(current_app.config.get("AI_PROVIDER", "openai")).lower().strip()
    if provider_name != "openai":
        raise AIConfigurationError(f"Unsupported AI provider: {provider_name}")

    api_key = str(current_app.config.get("AI_API_KEY", "")).strip()
    model = str(current_app.config.get("AI_MODEL", "")).strip()
    if not api_key:
        raise AIConfigurationError("AI_API_KEY is not configured.")
    if not model:
        raise AIConfigurationError("AI_MODEL is not configured.")

    return OpenAIProvider(
        api_key=api_key,
        model=model,
        api_base=str(current_app.config.get("AI_API_BASE", "https://api.openai.com/v1")),
        timeout=int(current_app.config.get("AI_TIMEOUT_SECONDS", 90)),
    )
