"""
OpenAI-compatible provider for any service that follows the OpenAI API format.
Supports: SiliconFlow (硅基流动), DeepSeek, Moonshot (月之暗面), ZhipuAI (智谱), etc.
"""
import json
import re
from datetime import datetime, timezone

from app.ai.base import AIProvider, AIProviderError, AnalysisResult
from app.ai.prompt_builder import build_analysis_prompt
from app.ai.claude_provider import _extract_json

# Known provider presets: (base_url, default_model, display_name)
COMPAT_PRESETS = {
    'siliconflow': (
        'https://api.siliconflow.cn/v1',
        'Qwen/Qwen2.5-7B-Instruct',
        '硅基流动 SiliconFlow',
    ),
    'deepseek': (
        'https://api.deepseek.com/v1',
        'deepseek-chat',
        'DeepSeek',
    ),
    'moonshot': (
        'https://api.moonshot.cn/v1',
        'moonshot-v1-8k',
        'Moonshot 月之暗面',
    ),
    'zhipu': (
        'https://open.bigmodel.cn/api/paas/v4',
        'glm-4-flash',
        'ZhipuAI 智谱',
    ),
}


class CompatProvider(AIProvider):
    """Generic OpenAI-compatible API provider."""

    def __init__(self, api_key: str, base_url: str, model: str,
                 display_name: str = 'Custom'):
        if not api_key:
            raise AIProviderError(f"API key for {display_name} is not set.")
        try:
            import openai
            self._client = openai.OpenAI(api_key=api_key, base_url=base_url)
        except ImportError:
            raise AIProviderError("openai package is not installed. Run: pip install openai")
        self._model = model
        self._display_name = display_name
        self._base_url = base_url

    @classmethod
    def from_preset(cls, preset_key: str, api_key: str,
                    model_override: str = '') -> 'CompatProvider':
        """Create a provider from a named preset."""
        if preset_key not in COMPAT_PRESETS:
            raise AIProviderError(f"Unknown preset: {preset_key}")
        base_url, default_model, name = COMPAT_PRESETS[preset_key]
        return cls(
            api_key=api_key,
            base_url=base_url,
            model=model_override or default_model,
            display_name=name,
        )

    @property
    def provider_name(self) -> str:
        return self._display_name

    @property
    def model_name(self) -> str:
        return self._model

    def analyze_article(self, title: str, text: str,
                        language: str = 'en') -> AnalysisResult:
        prompt = build_analysis_prompt(title, text, language)
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                max_tokens=512,
                messages=[
                    {"role": "system",
                     "content": "You are a news analysis assistant. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
            )
            raw = response.choices[0].message.content or ''
        except Exception as e:
            raise AIProviderError(f"{self._display_name} API error: {e}") from e

        data = _extract_json(raw)
        return AnalysisResult(
            summary=data.get('summary', ''),
            keywords=data.get('keywords', []),
            sentiment=data.get('sentiment', 'neutral'),
            confidence=float(data.get('confidence', 0.5)),
            provider=self._display_name,
            model=self._model,
            analyzed_at=datetime.now(timezone.utc).isoformat(),
            raw_response=raw,
        )

    def test_connection(self) -> tuple[bool, str]:
        try:
            self._client.chat.completions.create(
                model=self._model,
                max_tokens=10,
                messages=[{"role": "user", "content": "hi"}],
            )
            return True, f"Connected to {self._display_name} ({self._model})"
        except Exception as e:
            return False, str(e)
