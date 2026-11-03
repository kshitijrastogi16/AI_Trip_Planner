"""LLM construction for the travel-planning agent.

The application uses Groq BYOK: callers must provide a key for every request.
Keys are deliberately not read from environment variables or persisted here.
"""

from __future__ import annotations

from typing import Any

from utils.config_loader import load_config


class ConfigLoader:
    def __init__(self) -> None:
        self.config = load_config()

    def __getitem__(self, key: str) -> Any:
        return self.config[key]


class ModelLoader:
    """Create a Groq chat model using an explicitly supplied user API key."""

    def __init__(self, model_provider: str = "groq", api_key: str | None = None) -> None:
        provider = (model_provider or "").strip().lower()
        if provider != "groq":
            raise ValueError("Only the Groq provider is currently supported for BYOK.")

        key = (api_key or "").strip()
        if not key:
            raise ValueError("A Groq API key is required. Enter your key in the application.")

        self.model_provider = provider
        # Keep the secret out of repr/log output. Never write it to environment or disk.
        self._api_key = key
        self.config = ConfigLoader()

    def __repr__(self) -> str:
        return "ModelLoader(model_provider='groq', api_key_set=True)"

    def load_llm(self):
        """Construct a fresh provider client for the current request."""
        try:
            from langchain_groq import ChatGroq
        except ImportError as exc:
            raise RuntimeError(
                "Groq integration is unavailable. Install the project requirements."
            ) from exc

        model_name = self.config["llm"]["groq"]["model_name"]
        return ChatGroq(model=model_name, api_key=self._api_key)

    def validate_api_key(self) -> None:
        """Verify a supplied key by making a minimal authenticated model request."""
        llm = self.load_llm()
        llm.invoke("Reply with exactly: OK")
