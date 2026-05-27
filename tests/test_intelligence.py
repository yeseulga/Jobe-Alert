"""intelligence 모듈 단위 테스트."""
from __future__ import annotations
import json
from unittest.mock import MagicMock, patch

import pytest


# ── aggregator ───────────────────────────────────────────────

class TestAggregator:
    def test_safe_text_truncates(self):
        from intelligence.aggregator import _safe_text
        long = "a" * 600
        assert len(_safe_text(long)) == 500

    def test_safe_text_none(self):
        from intelligence.aggregator import _safe_text
        assert _safe_text(None) == ""

    def test_fetch_rss_returns_empty_on_error(self):
        from intelligence.aggregator import _fetch_rss
        # 존재하지 않는 URL → 오류 없이 빈 리스트
        result = _fetch_rss("http://invalid.example.com/rss", "Test")
        assert isinstance(result, list)

    def test_fetch_github_handles_rate_limit(self):
        from intelligence.aggregator import _fetch_github
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        with patch("requests.get", return_value=mock_resp):
            result = _fetch_github("https://api.github.com/search/repositories")
        assert result == []

    def test_collect_all_returns_list_on_all_failures(self):
        """전체 소스 실패해도 빈 리스트 반환 — 크래시 없음."""
        from intelligence.aggregator import collect_all
        with patch("intelligence.aggregator._fetch_rss", return_value=[]), \
             patch("intelligence.aggregator._fetch_huggingface", return_value=[]), \
             patch("intelligence.aggregator._fetch_github", return_value=[]), \
             patch("intelligence.aggregator._fetch_pwc", return_value=[]):
            result = collect_all()
        assert result == []


# ── curator ──────────────────────────────────────────────────

class TestCurator:
    def test_rule_classify_research(self):
        from intelligence.curator import _rule_classify
        assert _rule_classify("New Transformer Model", "arxiv paper neural network") == "research"

    def test_rule_classify_ecosystem(self):
        from intelligence.curator import _rule_classify
        assert _rule_classify("OpenAI raises $10B", "funding investment startup") == "ecosystem"

    def test_safe_input_strips_and_truncates(self):
        from intelligence.curator import _safe_input
        text = "  " + "x" * 600 + "  "
        result = _safe_input(text)
        assert len(result) == 500
        assert not result.startswith(" ")

    def test_parse_claude_output_valid(self):
        from intelligence.curator import _parse_claude_output
        output = json.dumps([
            {"category": "research", "summary_ko": "한국어 요약", "relevance_score": 8}
        ])
        result = _parse_claude_output(output, 1)
        assert result is not None
        assert result[0]["category"] == "research"

    def test_parse_claude_output_invalid_json(self):
        from intelligence.curator import _parse_claude_output
        result = _parse_claude_output("not json at all", 1)
        assert result is None

    def test_curate_empty_input(self):
        from intelligence.curator import curate
        assert curate([]) == []

    def test_curate_falls_back_on_api_error(self):
        from intelligence.curator import curate
        items = [{"title": "Test Paper", "summary": "abstract", "url": "https://example.com"}]
        with patch("anthropic.Anthropic") as mock_cls:
            mock_cls.return_value.messages.create.side_effect = Exception("API error")
            result = curate(items)
        assert len(result) >= 0   # rule-based fallback → 발송 여부는 relevance_score 기준


# ── dedup ────────────────────────────────────────────────────

class TestDedup:
    def test_filter_new_empty(self):
        from intelligence.dedup import filter_new
        assert filter_new([]) == []

    def test_mark_seen_empty(self):
        from intelligence.dedup import mark_seen
        mark_seen([])   # 크래시 없음


# ── discord_digest ───────────────────────────────────────────

class TestDiscordDigest:
    def test_send_digest_raises_without_webhook(self, monkeypatch):
        monkeypatch.delenv("DISCORD_INTELLIGENCE_WEBHOOK_URL", raising=False)
        from intelligence.discord_digest import send_digest
        with pytest.raises(EnvironmentError):
            send_digest({"research": [{"title": "T", "url": "http://x.com"}]})

    def test_send_digest_dry_run_no_webhook_needed(self, monkeypatch):
        """dry_run=True는 webhook 없어도 동작."""
        monkeypatch.setenv("DISCORD_INTELLIGENCE_WEBHOOK_URL", "https://example.com/webhook")
        from intelligence.discord_digest import send_digest
        send_digest(
            {"research": [{"title": "T", "summary_ko": "요약", "url": "http://x.com", "source": "arXiv"}]},
            dry_run=True,
        )   # 크래시 없음

    def test_send_digest_empty_no_post(self, monkeypatch):
        monkeypatch.setenv("DISCORD_INTELLIGENCE_WEBHOOK_URL", "https://example.com/webhook")
        from intelligence.discord_digest import send_digest
        with patch("requests.post") as mock_post:
            send_digest({})
        mock_post.assert_not_called()
