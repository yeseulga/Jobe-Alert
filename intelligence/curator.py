"""Claude Haiku로 아이템 분류 + 한국어 요약.

보안:
  - 각 아이템을 <item> XML 태그로 감싸 프롬프트 인젝션 차단
  - 제목/요약 500자 절단 (config.CURATOR_INPUT_MAX_CHARS)
  - Claude 출력 JSON 검증 (실패 시 rule-based fallback)
"""
from __future__ import annotations
import json
import os
import re

import anthropic

from .config import (
    CATEGORIES,
    CURATOR_BATCH_SIZE,
    CURATOR_INPUT_MAX_CHARS,
    CURATOR_MAX_TOKENS,
    CURATOR_MIN_RELEVANCE,
    CURATOR_MODEL,
    IMPACT_AREAS,
)

# ── Rule-based fallback 키워드 맵 ───────────────────────────

_RULE_KEYWORDS: dict[str, list[str]] = {
    "research": [
        "arxiv", "paper", "dataset", "benchmark", "model", "neural", "transformer",
        "llm", "diffusion", "multimodal", "training", "fine-tun", "rag", "retrieval",
        "huggingface", "github", "repository", "open-source", "weights",
    ],
    "skills": [
        "tutorial", "guide", "best practice", "how to", "prompt", "agent",
        "langchain", "llamaindex", "workflow", "pipeline", "deploy", "mcp",
        "tool use", "function calling", "anthropic", "openai api", "sdk",
    ],
    "model": [
        "benchmark", "performance", "token", "cost", "latency", "speed",
        "efficient", "quantiz", "compress", "ux", "user experience", "ax",
        "interface", "product", "chat", "assistant",
    ],
    "ecosystem": [
        "funding", "startup", "raise", "invest", "company", "release", "launch",
        "indie", "solo", "saas", "revenue", "mrr", "acquisition", "partnership",
        "google", "openai", "meta", "mistral", "cohere", "perplexity",
    ],
}


_IMPACT_KEYWORDS: dict[str, list[str]] = {
    "dev_workflow": [
        "ci/cd", "deploy", "dockerfile", "vscode", "cursor", "copilot", "ide",
        "github action", "devcontainer", "linting", "testing", "debug", "logging",
        "workflow", "pipeline", "automation", "code generation", "codegen",
    ],
    "prompt_eng": [
        "prompt", "chain-of-thought", "cot", "few-shot", "zero-shot", "instruction",
        "fine-tun", "rlhf", "dpo", "sft", "alignment", "evaluation", "eval",
        "benchmark", "hallucination", "output format", "structured output",
        "system prompt", "context window",
    ],
    "agent_design": [
        "agent", "agentic", "multi-agent", "tool use", "function calling",
        "memory", "retrieval", "rag", "react", "reflexion", "planning",
        "langchain", "llamaindex", "autogen", "crewai", "mcp", "orchestrat",
        "long-running", "autonomous",
    ],
    "monetize": [
        "saas", "revenue", "mrr", "arr", "product", "launch", "ship",
        "api service", "paid", "subscription", "monetize", "customer",
        "startup", "indie", "solo", "bootstrap", "profit", "market",
        "product hunt", "side project", "build in public",
    ],
    "portfolio": [
        "tutorial", "implementation", "how to", "build", "hands-on",
        "step by step", "project", "demo", "example", "notebook",
        "colab", "open source", "reproduce", "from scratch",
        "beginner", "practice", "exercise", "code along",
        # LLM 동작 분석 논문 — 면접에서 말할 수 있는 인사이트
        "we find that", "we show that", "empirical", "position bias",
        "lost in the middle", "context rot", "attention pattern",
        "long context", "needle in a haystack", "calibration",
        "hallucination", "in-context learning", "recency bias",
        "primacy bias", "distraction", "context length",
    ],
}


def _rule_classify(title: str, summary: str) -> str:
    text = (title + " " + summary).lower()
    scores = {cat: sum(1 for kw in kws if kw in text) for cat, kws in _RULE_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "research"


def _rule_impact(title: str, summary: str) -> list[str]:
    text = (title + " " + summary).lower()
    return [ia for ia, kws in _IMPACT_KEYWORDS.items() if any(kw in text for kw in kws)]


def _safe_input(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())[:CURATOR_INPUT_MAX_CHARS]


# ── Claude Haiku 큐레이션 ────────────────────────────────────

_SYSTEM_PROMPT = """당신은 특정 구독자를 위한 AI 엔지니어 성장 큐레이터입니다.
각 <item>을 분석해 JSON 배열로 응답하세요. 다른 텍스트는 출력하지 마세요.

구독자 프로파일:
- 비개발 도메인 5년 경력 후 AI 엔지니어로 전향 중인 한국인 (Python 초중급)
- RAG·에이전트·LLM 파인튜닝에 집중 학습 중
- 목표 1: 한국 AI 스타트업/빅테크 취업 (포트폴리오 구축 필요)
- 목표 2: AI 기반 1인 SaaS·인디 해커로 성장 (수익화 아이디어 탐색 중)
→ summary_ko와 apply_tip은 이 사람 관점에서 작성 (입문~중급 수준, 실용·취업·창업 연결)

카테고리:
- research: 논문, 모델, 데이터셋, 오픈소스
- skills: 기술 스킬, 방법론, 튜토리얼, 프롬프트
- model: 모델 릴리스·업데이트·벤치마크·성능 비교 (GPT/Claude/Gemini/Llama 등), 토큰 효율, AX/UX
- ecosystem: AI 회사 동향, 인디 AI 빌더, 스타트업, 투자·파트너십, 새 AI 제품 런치

impact_areas (해당하는 것 모두 선택, 없으면 빈 배열):
- dev_workflow: 개발 도구/환경/CI/배포/코드 자동화
- prompt_eng: 프롬프트/파인튜닝/평가/정렬
- agent_design: 에이전트/메모리/멀티에이전트/툴 사용
- monetize: 이 기술/아이디어로 제품·SaaS·API 서비스 만들어 수익화 가능
- portfolio: 포트폴리오·사이드 프로젝트로 바로 구현 가능, 면접에서 말할 수 있는 내용

응답 형식 (배열, 아이템 수 = 입력과 동일):
[{"category":"research","summary_ko":"한국어 3줄 요약","relevance_score":8,"impact_areas":["agent_design","portfolio"],"apply_tip":"지금 써먹기 팁"}, ...]

summary_ko: ① 무엇인지 ② 왜 중요한지 ③ 이 구독자에게 어떤 의미인지 (취업·창업 연결) 3문장
apply_tip: 취업 포트폴리오 또는 1인 SaaS 아이디어로 연결되는 실용 팁 1문장
relevance_score: 이 구독자 기준 유용도 1-10 (6 이상만 발송)
  → +1: MIT·Stanford·CMU·UC버클리·코넬·DeepMind·OpenAI·Anthropic·Microsoft Research 소속 논문
  → +1: RAG·에이전트·LLM 파인튜닝·추론 효율화·멀티에이전트 주제
  → +1: 실제 구현 가능한 튜토리얼·코드 포함·사이드 프로젝트 아이디어
  → +1: LLM 실제 동작 분석 논문 — "Lost in the Middle"(위치 편향), "Context Rot"(컨텍스트 성능 저하) 류
       즉, 위치 편향·주의력 패턴·환각 메커니즘·컨텍스트 한계·캘리브레이션·ICL 한계 등
       AI 엔지니어가 시스템 설계 시 반드시 알아야 하는 실험적 발견

apply_tip 작성 가이드 (LLM 동작 분석 논문의 경우):
  "Lost in the Middle" 스타일이면 → "중요 정보를 컨텍스트 앞뒤에 배치하는 프롬프트 전략 적용"
  환각 패턴 논문이면 → "RAG에서 이 조건일 때 검색 결과 재확인 로직 추가"
  이런 식으로 실무 시스템 설계에 직접 연결되는 팁 작성"""


def _parse_claude_output(text: str, count: int) -> list[dict] | None:
    """Claude 응답에서 JSON 파싱. 실패하면 None 반환. 아이템 수 불일치는 허용."""
    try:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return None
        parsed = json.loads(match.group())
        if not isinstance(parsed, list) or len(parsed) == 0:
            return None
        valid = []
        for item in parsed:
            if not all(k in item for k in ("category", "summary_ko", "relevance_score")):
                continue
            if item["category"] not in CATEGORIES:
                item["category"] = "research"
            item["relevance_score"] = int(item.get("relevance_score", 5))
            # impact_areas 검증 및 정규화
            raw_impacts = item.get("impact_areas", [])
            if not isinstance(raw_impacts, list):
                raw_impacts = []
            item["impact_areas"] = [ia for ia in raw_impacts if ia in IMPACT_AREAS]
            item["apply_tip"] = str(item.get("apply_tip", ""))[:120]
            valid.append(item)
        return valid if valid else None
    except (json.JSONDecodeError, ValueError, TypeError):
        return None


def curate(items: list[dict]) -> list[dict]:
    """아이템 분류 + 한국어 요약. Claude 실패 시 rule-based fallback."""
    if not items:
        return []

    api_key = os.getenv("ANTHROPIC_API_KEY")
    results: list[dict] = []

    for i in range(0, len(items), CURATOR_BATCH_SIZE):
        batch = items[i : i + CURATOR_BATCH_SIZE]
        enriched = _curate_batch(batch, api_key)
        results.extend(enriched)

    # 관련성 필터
    filtered = [r for r in results if r.get("relevance_score", 0) >= CURATOR_MIN_RELEVANCE]
    print(f"큐레이션 후 발송 대상: {len(filtered)}/{len(results)}건 (관련성 {CURATOR_MIN_RELEVANCE}+ 필터)")
    return filtered


def _curate_batch(batch: list[dict], api_key: str | None) -> list[dict]:
    """배치 처리 — Claude 실패 시 rule-based fallback."""
    if api_key:
        try:
            items_xml = "\n".join(
                f'<item id="{i}">'
                f'<title>{_safe_input(item["title"])}</title>'
                f'<summary>{_safe_input(item.get("summary", ""))}</summary>'
                f'</item>'
                for i, item in enumerate(batch)
            )
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model=CURATOR_MODEL,
                max_tokens=CURATOR_MAX_TOKENS,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": items_xml}],
            )
            parsed = _parse_claude_output(message.content[0].text, len(batch))
            if parsed:
                # 파싱 결과가 배치보다 적을 수 있음 — 매칭되는 것만 업데이트
                for item, meta in zip(batch, parsed):
                    item.update(meta)
                return batch
            print("  [Curator] Claude 출력 파싱 실패 → rule-based fallback")
        except anthropic.APIError as e:
            print(f"  [Curator] Claude API 오류: {e} → rule-based fallback")

    # Rule-based fallback
    for item in batch:
        item["category"] = _rule_classify(item["title"], item.get("summary", ""))
        item["summary_ko"] = item.get("summary", "")[:100]
        item["relevance_score"] = 7   # fallback은 기본 발송
        item["impact_areas"] = _rule_impact(item["title"], item.get("summary", ""))
        item["apply_tip"] = ""
    return batch
