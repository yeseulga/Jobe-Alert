"""AI Intelligence 피드 설정 — 소스, 카테고리, 경로."""
from pathlib import Path

# intelligence.db는 jobs.db와 분리된 경로
INTELLIGENCE_DB_PATH = Path(__file__).parent.parent / "intelligence.db"

# ── 카테고리 ──────────────────────────────────────────────────
CATEGORIES = {
    "research":    ("🔬", "Research", "최신 논문 + 뜨는 오픈소스"),
    "skills":      ("🛠️", "Skills & Practice", "AI 기술 스킬 + 방법론"),
    "model":       ("⚡", "Model & Efficiency", "모델 벤치마크 + 토큰 효율 + AX"),
    "ecosystem":   ("🏢", "Ecosystem", "AI 회사 동향 + 인디 AI 빌더"),
}

# ── 데이터 소스 ───────────────────────────────────────────────
# 각 항목: (name, url, type)
# type: "rss" | "github_api" | "hf_api" | "pwc_api"
SOURCES = [
    # ── 논문 (arXiv = 코넬대 운영, 전 세계 AI 논문 1차 공개 플랫폼) ─
    ("arXiv cs.AI",    "https://rss.arxiv.org/rss/cs.AI",                   "rss"),
    ("arXiv cs.LG",    "https://rss.arxiv.org/rss/cs.LG",                   "rss"),
    ("arXiv cs.CL",    "https://rss.arxiv.org/rss/cs.CL",                   "rss"),
    ("arXiv cs.IR",    "https://rss.arxiv.org/rss/cs.IR",                   "rss"),  # RAG·벡터검색·시맨틱 리트리벌
    ("HuggingFace",    "https://huggingface.co/api/daily_papers",            "hf_api"),
    ("GitHub AI",      "https://api.github.com/search/repositories",         "github_api"),
    # ── AI 회사 공식 블로그 ───────────────────────────────────────
    # Anthropic: 공개 RSS 없음 — 아래 미디어 소스가 Claude 릴리스 커버
    ("OpenAI News",      "https://openai.com/news/rss.xml",                    "rss"),
    ("Google AI Blog",   "https://blog.google/technology/ai/rss/",             "rss"),
    ("DeepMind Blog",    "https://deepmind.google/blog/rss.xml",               "rss"),  # Gemini·연구 발표
    ("Microsoft AI",     "https://blogs.microsoft.com/ai/feed/",               "rss"),  # Copilot·Azure AI
    # ── 모델 성능·릴리스 미디어 ──────────────────────────────────
    ("The Verge AI",     "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "rss"),
    ("Ars Technica",     "https://feeds.arstechnica.com/arstechnica/technology-lab",          "rss"),
    ("TechCrunch AI",    "https://techcrunch.com/tag/artificial-intelligence/feed/",          "rss"),
    # ── 대학 연구소 블로그 ───────────────────────────────────────
    ("BAIR Blog",        "https://bair.berkeley.edu/blog/feed.xml",            "rss"),  # UC버클리 AI 연구소
    # ── AI 엔지니어 실무 ─────────────────────────────────────────
    ("Simon Willison",   "https://simonwillison.net/atom/everything/",         "rss"),
    ("The Batch",        "https://www.deeplearning.ai/the-batch/feed/",        "rss"),  # Andrew Ng 뉴스레터
]

# GitHub Search API 파라미터
GITHUB_QUERY = "topic:ai created:>{date}&sort=stars&order=desc&per_page=10"

# Claude Haiku 설정
CURATOR_MODEL = "claude-haiku-4-5-20251001"
CURATOR_BATCH_SIZE = 5    # 배치 크기 줄여서 max_tokens 초과 방지
CURATOR_MAX_TOKENS = 2048  # 5개 × 약 200토큰/아이템
CURATOR_INPUT_MAX_CHARS = 500   # 프롬프트 인젝션 방지용 절단 길이
CURATOR_MIN_RELEVANCE = 6   # 이 점수 미만은 발송 안 함

# 영향 영역 (impact_area)
IMPACT_AREAS = {
    "dev_workflow":  "🔧 개발 워크플로우",
    "prompt_eng":    "💬 프롬프트 엔지니어링",
    "agent_design":  "🤖 에이전트 설계",
}

# 카테고리별 Discord embed에 표시할 최대 아이템 수
MAX_ITEMS_PER_CATEGORY = 3

# 전체 핫이슈 TOP N
TOP_PICKS_COUNT = 3

# Discord 발송 설정
DISCORD_RETRY_DELAYS = [1, 2, 4]   # 429 시 지수 백오프 (초)
