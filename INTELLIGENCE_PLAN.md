<!-- /autoplan restore point: /Users/gayeseul/.gstack/projects/yeseulga-Jobe-Alert/main-autoplan-restore-20260526-233109.md -->
# AI Intelligence Daily Digest — 계획 문서

<!-- AUTONOMOUS DECISION LOG -->
## Decision Audit Trail

| # | Phase | Decision | Classification | Principle | Rationale | Rejected |
|---|-------|----------|----------------|-----------|-----------|---------|
| 1 | CEO | 전제 수락 (Discord 9am, job-alert 레포, Approach B) | Mechanical | P6 (action) | 사용자가 D1에서 모든 전제 확인 | - |
| 2 | CEO | Approach B (RSS + Claude Haiku) 선택 | Mechanical | P1+P5 | 완성도 8/10, 기존 스택 재사용, 비용 최소 | Approach A (4/10), C (과엔지니어링) |
| 3 | CEO | 카테고리 7→4로 압축 | Mechanical | P5 (explicit) | Discord rate limit + 읽기 피로 방지 | 7개 카테고리 |
| 4 | CEO | AWS/RAG Phase 2로 defer | Mechanical | P3 (pragmatic) | MVP에 불필요, 30일 사용 후 전환 결정 | AWS 즉시 구현 |
| 5 | CEO | Claude fallback 전략 추가 | Mechanical | P1 (completeness) | API down 시 rule-based 분류 필요 | graceful fail without fallback |
| * | CEO | [USER CHALLENGE] 전체 모듈 vs daily_brief.py | USER_CHALLENGE | - | 서브에이전트: 취업 직결 액션 아이템으로 축소 권장 | 최종 게이트에서 사용자 결정 |
| 6 | Eng | sources/ 폴더 제거 → aggregator.py에 통합 | Mechanical | P4 (DRY) | 5개 소스 파일이 동일 패턴 반복 → config-driven 통합 | 별도 sources/ 폴더 |
| 7 | Eng | GitHub trending: Search API 우선, HTML 스크래핑 fallback | Mechanical | P5 (explicit) | HTML 스크래핑은 분기마다 깨짐, CI IP Cloudflare 차단 위험 | HTML 스크래핑 우선 |
| 8 | Eng | Claude 출력에 Pydantic 스키마 검증 추가 | Mechanical | P1 (completeness) | Haiku 부하 시 JSON 오염 발생, fallback 없으면 배치 전체 실패 | 검증 없음 |
| 9 | Eng | 프롬프트 인젝션 완화: XML 태그 + 500자 절단 | Mechanical | P1 (security) | arXiv 제목이 LLM 프롬프트에 직접 주입됨 | 미처리 |
| 10 | Eng | Discord 429 exponential backoff 추가 | Mechanical | P1 (completeness) | 4개 embed 동시 발송 시 rate limit 발생 가능 | 없음 |
| 11 | Eng | intelligence.db 경로 config.py에 명시 | Mechanical | P5 (explicit) | core/db.py 패턴 복사 시 jobs.db 덮어쓰기 위험 | 묵시적 경로 |
| 12 | Eng | secrets 미설정 startup guard 추가 | Mechanical | P1 (completeness) | 빈 문자열 webhook URL로 Discord 발송 실패 무언 | 없음 |



## 개요

job-alert 프로젝트에 **AI 엔지니어 성장 인텔리전스** 모듈을 추가한다.
매일 오전 9시 KST에 Discord로 최신 AI 기술 동향, 논문, 오픈소스, 방법론을 큐레이션하여 발송한다.

**목표:** 초보 개발자(5년 도메인 경력 + AI 전환 중)인 예슬이 AI 엔지니어로 최단 경로로 성장하도록 일일 정보 큐레이션 시스템 구축.

---

## 알림 카테고리 (7개)

| # | 이모지 | 카테고리 | 설명 |
|---|--------|----------|------|
| 1 | 🔥 | Hot Papers | arXiv, Papers with Code — 최신 핫한 논문 |
| 2 | 🚀 | Trending Open Source | GitHub Trending — AI/ML 뜨는 오픈소스 |
| 3 | 🛠️ | AI Skills & Techniques | 최신 기술 스킬 (RAG, Agents, MCP, etc.) |
| 4 | 🤔 | AI Engineering Thought | AI 엔지니어가 고민할 방법론·아키텍처 문제 |
| 5 | ⚡ | Token & Model Benchmarks | 토큰 효율, 모델 성능 벤치마크, 비용 최적화 |
| 6 | 🎨 | AX Trends | AI UX/AX — 요즘 뜨는 AI 사용자 경험 |
| 7 | 🏢+🦸 | Company & Solo Builder | AI 자체기술 회사 동향 + 1인 AI 스튜디오 트렌드 |

---

## 아키텍처

```
[Sources Layer]
  ├── arxiv_rss.py        → arXiv cs.AI/cs.LG/cs.CL (RSS)
  ├── huggingface.py      → HuggingFace Daily Papers API
  ├── github_trending.py  → GitHub Trending (웹 스크래핑)
  ├── papers_with_code.py → Papers with Code API
  └── blog_rss.py         → 회사 블로그 RSS (OpenAI, Anthropic, Google, Meta)

[Processing Layer]
  ├── dedup.py            → SQLite 기반 seen 추적 (중복 제거)
  └── curator.py          → Claude API로 카테고리 분류 + 한국어 요약

[Output Layer]
  └── discord_digest.py   → Discord embed 포맷터 + 웹훅 발송

[Entry Point]
  └── main_intelligence.py  또는  main.py --mode=intelligence
```

---

## 파일 구조

```
job-alert/
├── intelligence/
│   ├── __init__.py
│   ├── config.py           ← 소스 URL, 카테고리 정의
│   ├── dedup.py            ← SQLite intelligence.db (seen 아이템 추적)
│   ├── curator.py          ← Claude API: 분류 + 한국어 요약
│   ├── discord_digest.py   ← Discord 임베드 포맷터
│   └── sources/
│       ├── __init__.py
│       ├── arxiv_rss.py
│       ├── huggingface.py
│       ├── github_trending.py
│       ├── papers_with_code.py
│       └── blog_rss.py
│
├── main_intelligence.py    ← 독립 진입점
└── .github/workflows/
    └── intelligence.yml    ← 별도 GitHub Actions (cron 매일 00:00 UTC)
```

---

## 데이터 소스

### 무료 API / RSS (인증 불필요)
| 소스 | 방법 | 카테고리 |
|------|------|----------|
| arXiv | RSS feed (cs.AI, cs.LG, cs.CL, cs.CV) | Papers |
| HuggingFace Daily Papers | JSON API (papers.huggingface.co) | Papers |
| Papers with Code | REST API (paperswithcode.com/api) | Papers + OS |
| GitHub Trending | 웹 스크래핑 (github.com/trending) | Open Source |
| OpenAI Blog | RSS | Skills + Company |
| Anthropic Blog | RSS | Skills + Company |
| Google DeepMind | RSS | Company |
| Meta AI | RSS | Company |
| The Batch (Andrew Ng) | RSS | Skills |

### GitHub API (토큰 권장, 없어도 동작)
- Trending repos: topic:ai,machine-learning sort by stars (최근 1일)

---

## 큐레이션 로직 (Claude API)

```
입력: 원시 아이템 (제목 + 링크 + 초록/설명)
→ Claude Haiku (비용 최적화): 
   1. 카테고리 분류 (1~7)
   2. 한국어 요약 (2줄, 예슬 관점)
   3. AI 엔지니어 관련성 점수 (1-10)
→ 관련성 7점 이상만 Discord 발송 (카테고리별 top 2~3개)
```

**프롬프트 전략:**
- 배치 처리 (10개씩) → 비용 최소화
- Prompt caching (anthropic 라이브러리) → 캐시 재사용
- 총 비용 예상: ~$0.01/day (Haiku 기준)

---

## Discord 메시지 구조

```
📡 AI 엔지니어 인텔리전스 — 2026-05-26 (월)
 
🔥 [HOT PAPERS]
  • [논문제목](링크) — 한국어 요약 (2줄)
  
🚀 [TRENDING OS]
  • [레포명](링크) ⭐1.2k — 설명
  
🛠️ [AI SKILLS]
  • 주요 기술 업데이트
  
... (7개 카테고리)

💡 오늘의 AI 엔지니어링 고민거리:
  [방법론 질문 또는 아키텍처 딜레마]
```

---

## 스케줄링

**GitHub Actions** (`intelligence.yml`):
```yaml
schedule:
  - cron: '0 0 * * *'   # 매일 00:00 UTC = 09:00 KST
```

**로컬 launchd** (macOS 백업):
```xml
<key>StartCalendarInterval</key>
<dict><key>Hour</key><integer>9</integer></dict>
```

---

## AWS/RAG 선택적 확장 (Phase 2)

**현재 단계 (Phase 1):** GitHub Actions + SQLite — 충분, 비용 0
**확장 필요 시 (Phase 2):**
- AWS Lambda + EventBridge (서버리스 스케줄)
- DynamoDB (본 글 이력 + 사용자 반응 추적)
- S3 + Claude (RAG): "이 논문이 내 스킬셋과 어떻게 연결되나?" 개인화

**Phase 1 → 2 전환 조건:** Discord 반응 모니터링 후 필요시 전환

---

## 의존성 추가

```
# requirements.txt 추가
feedparser>=6.0      # 이미 있음
requests>=2.31       # 이미 있음
anthropic>=0.50      # 이미 있음
```

신규 의존성 없음 — 기존 스택 재사용.

---

## 완료 기준

- [ ] `intelligence/` 모듈 생성
- [ ] 5개+ 소스에서 일일 아이템 수집 (20~50개)
- [ ] Claude Haiku로 분류 + 한국어 요약
- [ ] Discord 7개 카테고리 임베드 발송
- [ ] `intelligence.yml` GitHub Actions 워크플로
- [ ] SQLite `intelligence.db` 중복 제거
- [ ] `.env.example` 업데이트 (DISCORD_INTELLIGENCE_WEBHOOK_URL)

---

## 리스크

| 리스크 | 심각도 | 완화 방법 |
|--------|--------|-----------|
| arXiv RSS 다운 | Low | feedparser timeout + 빈 섹션 graceful |
| GitHub 스크래핑 차단 | Medium | GitHub API fallback |
| Claude API 비용 초과 | Low | Haiku + 배치 처리 + 예산 캡 |
| Discord 웹훅 429 | Low | 카테고리별 분리 발송 |
