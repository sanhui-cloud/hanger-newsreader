import json
import re
from datetime import datetime, timezone

from app.ai.base import AIProvider, AIProviderError, AnalysisResult, TopicReportResult
from app.ai.prompt_builder import build_analysis_prompt, build_topic_report_prompt


class ClaudeProvider(AIProvider):
    def __init__(self, api_key: str, model: str = 'claude-haiku-4-5-20251001'):
        if not api_key:
            raise AIProviderError("Claude API key is not set. Please configure it in Settings.")
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise AIProviderError("anthropic package is not installed. Run: pip install anthropic")
        self._model = model

    @property
    def provider_name(self) -> str:
        return 'claude'

    @property
    def model_name(self) -> str:
        return self._model

    def analyze_article(self, title: str, text: str,
                        language: str = 'en',
                        output_language: str = 'English') -> AnalysisResult:
        prompt = build_analysis_prompt(title, text, language, output_language)
        try:
            message = self._client.messages.create(
                model=self._model,
                max_tokens=512,
                system="You are a news analysis assistant. Always respond with valid JSON only.",
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text
        except Exception as e:
            raise AIProviderError(f"Claude API error: {e}") from e

        return self._parse_response(raw)

    def generate_topic_report(
        self,
        title: str,
        keywords: list[str],
        articles: list[dict],
        output_language: str = 'English',
    ) -> TopicReportResult:
        prompt = build_topic_report_prompt(title, keywords, articles, output_language)
        try:
            message = self._client.messages.create(
                model=self._model,
                max_tokens=1800,
                system="You are a careful news intelligence analyst. Write concise Markdown reports.",
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text
        except Exception as e:
            raise AIProviderError(f"Claude API error: {e}") from e

        return TopicReportResult(
            report=raw.strip(),
            provider='claude',
            model=self._model,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def test_connection(self) -> tuple[bool, str]:
        try:
            self._client.messages.create(
                model=self._model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True, f"Connected ({self._model})"
        except Exception as e:
            return False, str(e)

    def _parse_response(self, raw: str) -> AnalysisResult:
        data = _extract_json(raw)
        return AnalysisResult(
            summary=data.get('summary', ''),
            keywords=data.get('keywords', []),
            sentiment=data.get('sentiment', 'neutral'),
            confidence=float(data.get('confidence', 0.5)),
            provider='claude',
            model=self._model,
            analyzed_at=datetime.now(timezone.utc).isoformat(),
            raw_response=raw,
        )


def _extract_json(text: str) -> dict:
    """Parse JSON from response, with regex fallback if model adds prose."""
    text = text.strip()
    # Remove markdown code fences if present
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Regex fallback: find first {...} block
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    raise AIProviderError(f"Could not parse JSON from AI response: {text[:200]}")
