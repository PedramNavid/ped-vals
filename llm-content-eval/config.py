import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Model configurations
MODELS = {
    "openai": {
        "model": "gpt-4-turbo-preview",
        "params": {
            "temperature": 0.7,
            "max_tokens": 500
        }
    },
    "anthropic": {
        "model": "claude-3-opus-20240229",
        "params": {
            "temperature": 0.7,
            "max_tokens": 500
        }
    },
    "google": {
        "model": "gemini-1.5-pro",
        "params": {
            "temperature": 0.7,
            "max_tokens": 500
        }
    }
}

# Pricing per 1K tokens (update with current pricing)
PRICING = {
    "openai": {
        "gpt-4-turbo-preview": {
            "input": 0.01,
            "output": 0.03
        }
    },
    "anthropic": {
        "claude-3-opus-20240229": {
            "input": 0.015,
            "output": 0.075
        }
    },
    "google": {
        "gemini-1.5-pro": {
            "input": 0.00125,
            "output": 0.005
        }
    }
}

# Database
DATABASE_URL = "sqlite:///./data/database.db"

# Application settings
APP_TITLE = "LLM Content Evaluation"
APP_VERSION = "1.0.0"
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"