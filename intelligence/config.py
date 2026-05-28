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
# type: "rss" | "github_api" | "hf_api"
SOURCES = [
    # ── 논문 (arXiv = 코넬대 운영) ─────────────────────────────
    ("arXiv cs.AI",    "https://rss.arxiv.org/rss/cs.AI",                   "rss"),
    ("arXiv cs.LG",    "https://rss.arxiv.org/rss/cs.LG",                   "rss"),
    ("arXiv cs.CL",    "https://rss.arxiv.org/rss/cs.CL",                   "rss"),
    ("arXiv cs.IR",    "https://rss.arxiv.org/rss/cs.IR",                   "rss"),  # RAG·벡터검색·시맨틱 리트리벌
    ("HuggingFace",    "https://huggingface.co/api/daily_papers",            "hf_api"),
    ("GitHub AI",      "https://api.github.com/search/repositories",         "github_api"),
    # ── AI 회사 공식 블로그 ─────────────────────────────────────
    ("OpenAI News",      "https://openai.com/news/rss.xml",                    "rss"),
    ("Google AI Blog",   "https://blog.google/technology/ai/rss/",             "rss"),
    ("DeepMind Blog",    "https://deepmind.google/blog/rss.xml",               "rss"),
    ("Microsoft AI",     "https://blogs.microsoft.com/ai/feed/",               "rss"),
    # ── 모델 성능·릴리스 미디어 ────────────────────────────────
    ("The Verge AI",     "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "rss"),
    ("Ars Technica",     "https://feeds.arstechnica.com/arstechnica/technology-lab",          "rss"),
    ("TechCrunch AI",    "https://techcrunch.com/tag/artificial-intelligence/feed/",          "rss"),
    # ── 대학 연구소 ─────────────────────────────────────────────
    ("BAIR Blog",        "https://bair.berkeley.edu/blog/feed.xml",            "rss"),  # UC버클리
    # ── 빌더 커뮤니티 (1인 사업자 관점) ────────────────────────
    ("Hacker News AI",   "https://hnrss.org/newest?q=LLM+agent&count=10",     "rss"),  # 실전 빌더 토론
    ("Product Hunt",     "https://www.producthunt.com/feed",                   "rss"),  # 매일 새 AI 제품 런치
    # ── AI 엔지니어 실무 심화 ───────────────────────────────────
    ("Towards DS",       "https://towardsdatascience.com/feed",                "rss"),  # 구현 중심 튜토리얼
    ("Ahead of AI",      "https://magazine.sebastianraschka.com/feed",         "rss"),  # LLM 아키텍처 심화
    ("Simon Willison",   "https://simonwillison.net/atom/everything/",         "rss"),
    ("The Batch",        "https://www.deeplearning.ai/the-batch/feed/",        "rss"),
]

# GitHub Search API 파라미터
GITHUB_QUERY = "topic:ai created:>{date}&sort=stars&order=desc&per_page=10"

# Claude Haiku 설정
CURATOR_MODEL = "claude-haiku-4-5-20251001"
CURATOR_BATCH_SIZE = 5
CURATOR_MAX_TOKENS = 2048
CURATOR_INPUT_MAX_CHARS = 500
CURATOR_MIN_RELEVANCE = 6

# 영향 영역 (impact_area)
IMPACT_AREAS = {
    "dev_workflow":  "🔧 개발 워크플로우",
    "prompt_eng":    "💬 프롬프트 엔지니어링",
    "agent_design":  "🤖 에이전트 설계",
    "monetize":      "💰 수익화 가능",      # 제품·SaaS로 만들 수 있는 내용
    "portfolio":     "🎯 포트폴리오 적합",  # 취업 면접·포트폴리오에 쓸 수 있는 내용
}

# 카테고리별 Discord embed에 표시할 최대 아이템 수
MAX_ITEMS_PER_CATEGORY = 3

# 전체 핫이슈 TOP N
TOP_PICKS_COUNT = 3

# Discord 발송 설정
DISCORD_RETRY_DELAYS = [1, 2, 4]
