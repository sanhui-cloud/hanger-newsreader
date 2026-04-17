import json
import re
from datetime import datetime, timezone

from app.ai.base import AIProvider, AIProviderError, AnalysisResult
from app.ai.prompt_builder import build_analysis_prompt
from app.ai.claude_provider import _extract_json


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str = 'gpt-4o-mini'):
        if not api_key:
            raise AIProviderError("OpenAI API key is not set. Please configure it in Settings.")
        try:
            import openai
            self._client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise AIProviderError("openai package is not installed. Run: pip install openai")
        self._model = model

    @property
    def provider_name(self) -> str:
        return 'openai'

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
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system",
                     "content": "You are a news analysis assistant. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
            )
            raw = response.choices[0].message.content or ''
        except Exception as e:
            raise AIProviderError(f"OpenAI API error: {e}") from e

        data = _extract_json(raw)
        return AnalysisResult(
            summary=data.get('summary', ''),
            keywords=data.get('keywords', []),
            sentiment=data.get('sentiment', 'neutral'),
            confidence=float(data.get('confidence', 0.5)),
            provider='openai',
            model=self._model,
            analyzed_at=datetime.now(timezone.utc).isoformat(),
            raw_response=raw,
        )

    def test_connection(self) -> tuple[bool, str]:
        try:
            models = self._client.models.list()
            return True, f"Connected ({self._model})"
        except Exception as e:
            return False, str(e)
