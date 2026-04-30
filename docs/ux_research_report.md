# Global News Reader UX Research & Upgrade Report

Date: 2026-04-30

## Scope

This project is an RSS/news reader and AI-assisted news analysis desktop tool. It is not a WeChat-specific tool, so the comparison set below focuses on RSS readers, feed aggregators, and AI news-reading workflows.

## GitHub References

- [Fluent Reader](https://github.com/yang991178/fluent-reader): modern desktop RSS reader. Useful reference points: full dark mode, read-status filtering, starred articles, folder groupings, OPML import/export, full-content reading, keyboard shortcuts, regex rules, and background fetching.
- [Folo](https://github.com/RSSNext/Folo): AI RSS reader. Useful reference points: curated information hub, favorites, AI translation/summary, and support for more than plain text.
- [FreshRSS](https://github.com/FreshRSS/FreshRSS): self-hostable news aggregator. Useful reference points: durable server-side aggregation, multi-source reliability, and long-term reading history.
- [NetNewsWire](https://github.com/Ranchero-Software/NetNewsWire): free open-source macOS/iOS feed reader. Useful reference points: fast native reading, feed-format coverage, and simple bug/feature workflow.
- [RSSHub](https://github.com/DIYgod/RSSHub): large RSS route ecosystem. Useful reference points: expanding source coverage and pairing source discovery with reader workflows.

## Original UX Findings

- The top toolbar rendered far too tall, leaving a large blank band before the actual reading area.
- The center list showed only category, title, and metadata, so users could not quickly judge article relevance without opening each item.
- There was no read/unread or saved state, which made repeated daily use feel like browsing a static dump rather than managing a queue.
- AI existed only as a per-article action; there was no sense of queue health, AI coverage, or batch workflow.
- The detail pane was mostly blank before selection and had weak action grouping.
- Search only covered title/summary, missing source names and extracted full text.
- Source filtering existed but lacked quick select/clear controls and count feedback.

## Design Direction

The upgraded interface should behave like a compact news workbench:

- A tight command bar for refresh, search, status filters, AI action, and settings.
- A briefing dashboard that shows total, unread, saved, AI-ready, and today counts.
- A queue action area for batch AI analysis and missing-text extraction.
- A richer timeline with unread markers, snippets, full-text badges, AI badges, and saved state.
- A detail pane that keeps reading actions together: save, mark unread, export Markdown, open link, extract text, and analyze.

## Implemented Changes

- Added persistent article state: `is_read`, `is_favorite`, and `read_at`, with migration support for existing databases.
- Added repository query support for status filters: all, unread, saved, and analyzed.
- Added dashboard statistics and queue queries for AI and missing full text.
- Rebuilt the main layout into toolbar, briefing panel, three reading panes, and status bar.
- Added `InsightPanel` with metrics and queue actions.
- Added toolbar status filters and expanded search over title, summary, full text, and source name.
- Added richer article cards with unread dot, snippet preview, saved badge, full-text badge, and AI badge.
- Added quick source selection controls and category source counts.
- Added detail actions: save/unsave, mark unread, export Markdown, open link.
- Added batch AI queue analysis for the latest un-analyzed articles in the current source/search scope.
- Added missing full-text extraction queue action.
- Fixed the auto-refresh callback path so scheduled refresh uses the same safe fetch flow as the manual refresh button.
- Added AI output language selection for summaries, keywords, and generated topic reports.
- Added keyword-based topic reports with persistent storage, a `Reports` viewer tab, and Markdown export.
- Added optional automatic topic report generation after refresh when configured keywords match fetched articles.
- Added source health tracking for each RSS source: last fetch status, latest article freshness, consecutive failures, stored count, and missing full-text count.
- Added cleanup rules to cap local storage by article age, per-source count, and global article count while preserving favorites.

## Verification

- Before screenshot: `assets/ui_before.png`
- After screenshot: `assets/ui_after.png`
- Syntax check: `syntax ok: 32 files`
- Database initialization smoke test: seeded 12 default sources and returned article stats.
- Migration smoke test: old-style article table was upgraded with `is_read`, `is_favorite`, and `read_at`.
- Report schema smoke test: created and read back a generated topic report record.
- Source health smoke test: health rows, missing-text counts, and cleanup result keys validated.

## Next Opportunities

- OPML import/export for subscription portability.
- Keyboard shortcuts for next article, save, mark unread, and analyze.
- AI daily digest generation across selected sources.
- Rule engine for auto-save, auto-hide, or auto-analyze based on title/source/keyword patterns.
- Per-source health panel with last fetch time, error rate, and article yield.
- Topic report scheduling with separate cadences for daily, weekly, and breaking-event reports.
- Per-source retry/backoff controls and health history charts.
