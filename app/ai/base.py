from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AnalysisResult:
    summary: str
    keywords: list[str]
    sentiment: str          # positive | negative | neutral | mixed
    confidence: float       # 0.0–1.0
    provider: str
    model: str
    analyzed_at: str        # ISO8601
    raw_response: str = field(repr=False, default='')


class AIProviderError(Exception):
    pass


class AIProvider(ABC):
    @abstractmethod
    def analyze_article(self, title: str, text: str,
                        language: str = 'en') -> AnalysisResult:
        """Raises AIProviderError on failure."""

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """Returns (success, message)."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...


def get_provider(settings: dict) -> AIProvider:
    """Factory: returns concrete AIProvider based on settings['ai_provider']."""
    provider = settings.get('ai_provider', 'claude').lower()
    if provider == 'claude':
        from app.ai.claude_provider import ClaudeProvider
        return ClaudeProvider(
            api_key=settings.get('claude_api_key', ''),
            model=settings.get('claude_model', 'claude-haiku-4-5-20251001'),
        )
    elif provider == 'openai':
        from app.ai.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=settings.get('openai_api_key', ''),
            model=settings.get('openai_model', 'gpt-4o-mini'),
        )
    elif provider in ('siliconflow', 'deepseek', 'moonshot', 'zhipu'):
        from app.ai.compat_provider import CompatProvider
        return CompatProvider.from_preset(
            preset_key=provider,
            api_key=settings.get(f'{provider}_api_key', ''),
            model_override=settings.get(f'{provider}_model', ''),
        )
    elif provider == 'custom':
        from app.ai.compat_provider import CompatProvider
        return CompatProvider(
            api_key=settings.get('custom_api_key', ''),
            base_url=settings.get('custom_base_url', ''),
            model=settings.get('custom_model', ''),
            display_name=settings.get('custom_name', 'Custom'),
        )
    else:
        raise AIProviderError(f"Unknown AI provider: {provider}")
