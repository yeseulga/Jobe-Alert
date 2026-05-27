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
    ("arXiv cs.AI",    "https://rss.arxiv.org/rss/cs.AI",                   "rss"),
    ("arXiv cs.LG",    "https://rss.arxiv.org/rss/cs.LG",                   "rss"),
    ("arXiv cs.CL",    "https://rss.arxiv.org/rss/cs.CL",                   "rss"),
    ("HuggingFace",    "https://huggingface.co/api/daily_papers",            "hf_api"),
    ("GitHub AI",      "https://api.github.com/search/repositories",         "github_api"),
    # 블로그 RSS — 공식 피드 URL (변경 시 여기만 수정)
    ("OpenAI News",    "https://openai.com/news/rss.xml",                    "rss"),
    ("Google AI Blog", "https://blog.google/technology/ai/rss/",             "rss"),
    ("Simon Willison", "https://simonwillison.net/atom/everything/",         "rss"),  # AI 엔지니어 실무 블로그
    ("The Batch",      "https://www.deeplearning.ai/the-batch/feed/",        "rss"),  # Andrew Ng 뉴스레터
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

# Discord 발송 설정
DISCORD_RETRY_DELAYS = [1, 2, 4]   # 429 시 지수 백오프 (초)
