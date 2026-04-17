MAX_TEXT_CHARS = 4000


def build_analysis_prompt(title: str, text: str, language: str = 'en') -> str:
    """
    Build a prompt requesting JSON analysis of a news article.
    Truncates text to MAX_TEXT_CHARS to avoid token overruns.
    """
    truncated = text[:MAX_TEXT_CHARS]
    if len(text) > MAX_TEXT_CHARS:
        truncated += '\n[...text truncated...]'

    lang_note = f" (original language: {language})" if language != 'en' else ''

    return f"""Analyze the following news article{lang_note} and respond with ONLY a JSON object (no other text).

Article Title: {title}

Article Text:
{truncated}

Respond with this exact JSON structure:
{{
  "summary": "2-3 sentence summary of the article in English",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "sentiment": "positive|negative|neutral|mixed",
  "confidence": 0.85
}}

Rules:
- summary: Always in English, 2-3 sentences, factual
- keywords: Exactly 5 most important terms/phrases from the article
- sentiment: One of exactly: positive, negative, neutral, mixed
- confidence: Float 0.0-1.0, your confidence in the sentiment label
- Respond ONLY with the JSON object, no markdown fences, no explanation"""
