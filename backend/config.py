"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

def _parse_model_list(value: str | None) -> list[str]:
  """Parse a comma-separated list of model ids."""
  if not value:
    return []
  return [model.strip() for model in value.split(",") if model.strip()]


# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Council members - list of OpenRouter model identifiers
COUNCIL_MODELS = _parse_model_list(os.getenv("COUNCIL_MODELS")) or [
    "anthropic/claude-haiku-4.5",
    "google/gemini-3-flash-preview",
    "openai/gpt-5-mini",
    "x-ai/grok-4.1-fast",
]

# Chairman model - synthesizes final response (defaults to first council model if not set)
CHAIRMAN_MODEL = os.getenv("CHAIRMAN_MODEL") or COUNCIL_MODELS[0]

# Reasoning / thinking effort (e.g., "medium", "high" for models that support it)
REASONING_EFFORT = (os.getenv("REASONING_EFFORT") or "medium").strip().lower() or None

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
