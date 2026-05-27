"""
E2E 통합 테스트
전체 파이프라인: 수집 → 필터 → 자소서 → 기회 탐색

실행:
  pytest tests/test_e2e.py -v
  pytest tests/test_e2e.py -v -k "test_profile"   # 특정 테스트만
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
import pytest
import yaml

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


# ============================================================
# 프로파일/기준 파일 테스트
# ============================================================

class TestProfileFiles:
    """profile/ 폴더의 필수 파일이 올바른 형식인지 확인"""

    def test_me_md_exists(self):
        assert (ROOT / "profile" / "me.md").exists(), "profile/me.md 없음"

    def test_criteria_yaml_exists(self):
        assert (ROOT / "profile" / "criteria.yaml").exists(), "profile/criteria.yaml 없음"

    def test_target_companies_yaml_exists(self):
        assert (ROOT / "profile" / "target_companies.yaml").exists(), "profile/target_companies.yaml 없음"

    def test_criteria_has_required_keys(self):
        with open(ROOT / "profile" / "criteria.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "include_keywords" in data, "criteria.yaml에 include_keywords 없음"
        assert "work" in data, "criteria.yaml에 work 없음"
        assert "locations" in data["work"], "criteria.yaml에 work.locations 없음"

    def test_target_companies_has_entries(self):
        with open(ROOT / "profile" / "target_companies.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        companies = data.get("companies", [])
        assert len(companies) > 0, "target_companies.yaml에 회사 없음"
        for c in companies:
            assert "name" in c, f"회사 항목에 name 없음: {c}"
            assert "careers_url" in c, f"회사 항목에 careers_url 없음: {c['name']}"

    def test_criteria_direct_check_has_urls(self):
        with open(ROOT / "profile" / "criteria.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        direct = data.get("direct_check_companies", [])
        assert len(direct) > 0, "direct_check_companies 없음"
        for company in direct:
            assert company.get("careers_url"), f"{company['name']}의 careers_url 없음"


# ============================================================
# 자소서 파이프라인 테스트
# ============================================================

class TestCVPipeline:
    """cv/ 폴더 구조 및 파이프라인 파일 확인"""

    def test_experiences_md_exists(self):
        assert (ROOT / "cv" / "experiences.md").exists(), "cv/experiences.md 없음"

    def test_experiences_md_has_content(self):
        content = (ROOT / "cv" / "experiences.md").read_text(encoding="utf-8")
        assert len(content.strip()) > 100, "cv/experiences.md 내용이 너무 짧음 — 경험을 채워주세요"

    def test_pipeline_md_exists(self):
        assert (ROOT / "cv" / "PIPELINE.md").exists(), "cv/PIPELINE.md 없음"

    def test_generated_dir_can_be_created(self):
        generated = ROOT / "cv" / "generated" / "companies"
        generated.mkdir(parents=True, exist_ok=True)
        assert generated.exists()


# ============================================================
# 기회 (부트캠프/공모전) 테스트
# ============================================================

class TestOpportunities:
    """opportunities/ 폴더 구조 확인"""

    def test_bootcamps_yaml_exists(self):
        assert (ROOT / "opportunities" / "bootcamps.yaml").exists()

    def test_competitions_yaml_exists(self):
        assert (ROOT / "opportunities" / "competitions.yaml").exists()

    def test_bootcamps_has_fastcampus(self):
        with open(ROOT / "opportunities" / "bootcamps.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        providers = [b["provider"] for b in data.get("bootcamps", [])]
        assert "패스트캠퍼스" in providers, "bootcamps.yaml에 패스트캠퍼스 없음"

    def test_bootcamps_has_kernel_academy(self):
        with open(ROOT / "opportunities" / "bootcamps.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        providers = [b["provider"] for b in data.get("bootcamps", [])]
        assert "커널아카데미" in providers, "bootcamps.yaml에 커널아카데미 없음 (중요!)"

    def test_bootcamps_have_cost_info(self):
        with open(ROOT / "opportunities" / "bootcamps.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for camp in data.get("bootcamps", []):
            assert "cost_range" in camp, f"{camp['name']}에 cost_range 없음"

    def test_competitions_have_prize_info(self):
        with open(ROOT / "opportunities" / "competitions.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for comp in data.get("competitions", []):
            assert "prize" in comp, f"{comp['name']}에 prize 없음"


# ============================================================
# 스크래퍼 임포트 테스트
# ============================================================

class TestScraperImports:
    """모든 스크래퍼가 임포트 가능한지 확인"""

    def test_import_saramin(self):
        from scrapers import saramin
        assert hasattr(saramin, "scrape")

    def test_import_jobkorea(self):
        from scrapers import jobkorea
        assert hasattr(jobkorea, "scrape")

    def test_import_programmers(self):
        from scrapers import programmers
        assert hasattr(programmers, "scrape")

    def test_import_linkedin(self):
        from scrapers import linkedin
        assert hasattr(linkedin, "scrape")

    def test_import_wanted(self):
        from scrapers import wanted
        assert hasattr(wanted, "scrape")

    def test_import_remember(self):
        from scrapers import remember
        assert hasattr(remember, "scrape")

    def test_import_rocketpunch(self):
        from scrapers import rocketpunch
        assert hasattr(rocketpunch, "scrape")


# ============================================================
# 필터 로직 테스트
# ============================================================

class TestFilterLogic:
    """필터링 및 점수 산정 로직 검증"""

    def setup_method(self):
        from core.filter import filter_and_score
        self.filter_and_score = filter_and_score

    def _make_job(self, title: str, description: str = "", location: str = "서울") -> dict:
        return {
            "platform": "테스트",
            "title": title,
            "company": "테스트 회사",
            "position": title,
            "location": location,
            "deadline": "",
            "salary": "",
            "url": f"https://test.com/{title}",
            "description": description,
        }

    def test_llm_job_passes_filter(self):
        jobs = [self._make_job("LLM 엔지니어 모집")]
        result = self.filter_and_score(jobs)
        assert len(result) > 0, "LLM 공고가 필터에서 제외됨"

    def test_rag_job_passes_filter(self):
        jobs = [self._make_job("RAG 기반 AI 개발자")]
        result = self.filter_and_score(jobs)
        assert len(result) > 0

    def test_backend_job_excluded(self):
        jobs = [self._make_job("백엔드 개발자 (Python)")]
        result = self.filter_and_score(jobs)
        assert len(result) == 0, "백엔드 공고가 필터를 통과함"

    def test_llm_scores_higher_than_ai(self):
        jobs = [
            self._make_job("LLM 엔지니어", "LLM RAG Agent 기반"),
            self._make_job("AI 개발자", "AI 자동화"),
        ]
        result = self.filter_and_score(jobs)
        if len(result) >= 2:
            assert result[0]["score"] >= result[1]["score"], "LLM 공고가 AI 공고보다 점수가 낮음"

    def test_region_filter_is_per_scraper(self):
        """지역 필터는 각 스크래퍼에서 처리 (filter_and_score는 키워드만 담당)."""
        from scrapers.saramin import _is_in_allowed_region
        assert _is_in_allowed_region({"location": "서울"}) is True
        assert _is_in_allowed_region({"location": "판교"}) is True
        assert _is_in_allowed_region({"location": "부산"}) is False


# ============================================================
# CLAUDE.md 하네스 테스트
# ============================================================

class TestHarness:
    """CLAUDE.md 하네스 파일 완전성 확인"""

    def test_claude_md_exists(self):
        assert (ROOT / "CLAUDE.md").exists(), "CLAUDE.md 없음 — 하네스 파일이 필요합니다"

    def test_claude_md_has_required_sections(self):
        content = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        required = [
            "profile/me.md",
            "profile/criteria.yaml",
            "cv/experiences.md",
            "/fork prompt",
            "/gen cv",
        ]
        for section in required:
            assert section in content, f"CLAUDE.md에 '{section}' 섹션 없음"

    def test_prompts_dir_exists(self):
        assert (ROOT / "prompts").is_dir(), "prompts/ 디렉토리 없음"

    def test_prompt_templates_exist(self):
        assert (ROOT / "prompts" / "company_search.md").exists()
        assert (ROOT / "prompts" / "cover_letter.md").exists()
