import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-6")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")

SUPPORTED_PLATFORMS = ["kling"]
PLATFORM = "kling"
MODE = "image_to_video"  # всегда


def get_llm_client():
    if LLM_PROVIDER == "openai":
        from openai import OpenAI
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY не задан в .env файле")
        return OpenAI(api_key=OPENAI_API_KEY)
    elif LLM_PROVIDER == "anthropic":
        import anthropic
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY не задан в .env файле")
        return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    else:
        raise ValueError(f"Неизвестный провайдер: {LLM_PROVIDER}. Используйте 'openai' или 'anthropic'")


def get_model_name():
    if LLM_PROVIDER == "openai":
        return OPENAI_MODEL
    return ANTHROPIC_MODEL
