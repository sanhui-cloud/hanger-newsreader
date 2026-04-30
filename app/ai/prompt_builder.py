MAX_TEXT_CHARS = 4000
MAX_REPORT_ARTICLE_CHARS = 1100


def _output_language_note(output_language: str, fallback_language: str = 'en') -> str:
    if output_language.lower().startswith('original'):
        return f"the original article language ({fallback_language})"
    return output_language


def build_analysis_prompt(
    title: str,
    text: str,
    language: str = 'en',
    output_language: str = 'English',
) -> str:
    """
    Build a prompt requesting JSON analysis of a news article.
    Truncates text to MAX_TEXT_CHARS to avoid token overruns.
    """
    truncated = text[:MAX_TEXT_CHARS]
    if len(text) > MAX_TEXT_CHARS:
        truncated += '\n[...text truncated...]'

    lang_note = f" (original language: {language})" if language != 'en' else ''
    output_note = _output_language_note(output_language, language)

    return f"""Analyze the following news article{lang_note} and respond with ONLY a JSON object (no other text).

Article Title: {title}

Article Text:
{truncated}

Respond with this exact JSON structure:
{{
  "summary": "2-3 sentence summary of the article in {output_note}",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "sentiment": "positive|negative|neutral|mixed",
  "confidence": 0.85
}}

Rules:
- summary: Always in {output_note}, 2-3 sentences, factual
- keywords: Exactly 5 most important terms/phrases from the article, translated to {output_note} when natural
- sentiment: One of exactly: positive, negative, neutral, mixed
- confidence: Float 0.0-1.0, your confidence in the sentiment label
- Respond ONLY with the JSON object, no markdown fences, no explanation"""


def build_topic_report_prompt(
    title: str,
    keywords: list[str],
    articles: list[dict],
    output_language: str = 'English',
) -> str:
    """Build a multi-article report prompt. The response should be Markdown."""
    output_note = _output_language_note(output_language)
    keyword_text = ', '.join(keywords)
    article_blocks = []
    for idx, article in enumerate(articles, start=1):
        text = article.get('full_text') or article.get('summary') or ''
        text = ' '.join(text.split())
        if len(text) > MAX_REPORT_ARTICLE_CHARS:
            text = text[:MAX_REPORT_ARTICLE_CHARS].rstrip() + ' [...truncated...]'
        article_blocks.append(
            f"""[{idx}]
Title: {article.get('title', '')}
Source: {article.get('source_name', '')}
Published: {article.get('published_at', '')}
URL: {article.get('url', '')}
Text: {text}"""
        )

    return f"""Create a concise intelligence-style news report in Markdown.

Report title: {title}
Tracked keywords: {keyword_text}
Output language: {output_note}

Articles:
{chr(10).join(article_blocks)}

Requirements:
- Write all human-facing prose in {output_note}.
- Do not invent facts beyond the supplied articles.
- Merge repeated facts, explain how articles relate, and call out uncertainty.
- Keep it useful for a busy reader.
- Include these Markdown sections:
  # {title}
  ## Executive Brief
  ## What Happened
  ## Timeline
  ## Key Signals
  ## Open Questions
  ## Related Articles
- In Related Articles, include source names and URLs when available."""
