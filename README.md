# 📬 AI 기반 맞춤 채용 공고 추천 및 자동 메일 발송

Python 3.11+ 기반. 사람인(Saramin) 수집 → 필터/점수 → SQLite 중복제거 → Gmail 발송 → GitHub Actions 스케줄.

## 빠른 시작

1) 의존성 설치
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) 환경설정
```bash
cp .env.example .env
```
.env에 Gmail 앱 비밀번호, 수신자 등 입력.

3) 실행
```bash
python -m job_alert.main
```

## 구조
```
job_alert/
  scrapers/saramin.py   # 사람인 수집
  filtering.py          # 포함/제외 키워드 필터 + 점수
  db.py                 # SQLite 중복 방지
  emailer.py            # 템플릿 + Gmail 발송
  ocr.py                # OCR (이미지 → 텍스트)
  main.py               # 엔드포인트
```

## GitHub Actions
`.github/workflows/job-alert.yml` 가 평일 오전 8시(KST) 발송 스케줄을 수행합니다.  
레포 Secrets로 아래를 등록하세요:
- `GMAIL_SENDER`, `GMAIL_APP_PASSWORD`, `MAIL_TO`, `RECIPIENT_NAME`

## 메모
- 사람인 마크업 변경 시 셀렉터가 깨질 수 있습니다. 예외는 무시하고 가능한 항목만 수집합니다.
- 향후 `wanted`, `jobkorea`, `programmers`, `remember`, `linkedin(RSS)` 스크레이퍼를 추가할 수 있도록 구조화되어 있습니다.
# 📬 AI 기반 맞춤 채용 공고 추천 및 자동 메일 발송 시스템

> 평일 오전 8시, 맞춤 IT 채용 공고를 자동으로 이메일로 받아보세요.

---

## 📁 프로젝트 구조

```
job-alert/
├── main.py                    # 메인 실행 스크립트
├── requirements.txt           # Python 의존성
├── .env                       # 환경 변수 (로컬)
├── .env.example               # 환경 변수 예시
├── jobs.db                    # SQLite 중복 방지 DB
│
├── core/
│   ├── config.py              # 키워드 설정 및 가중치
│   ├── filter.py              # 키워드 필터링 + 점수 산정
│   ├── db.py                  # SQLite 중복 방지 모듈
│   ├── mailer.py              # 이메일 템플릿 + Gmail SMTP 발송
│   ├── ocr.py                 # OCR 처리 (pytesseract)
│   └── text_cleaner.py        # 텍스트 정제 유틸리티
│
├── scrapers/
│   ├── saramin.py             # 사람인 (requests + BS4)
│   ├── jobkorea.py            # 잡코리아 (requests + BS4)
│   ├── programmers.py         # 프로그래머스 (JSON API)
│   ├── linkedin.py            # LinkedIn (RSS 피드)
│   ├── wanted.py              # 원티드 (공개 API)
│   └── remember.py            # 리멤버 (Playwright + 로그인)
│
└── .github/
    └── workflows/
        └── job-alert.yml      # GitHub Actions 자동 실행
```

---

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
cd job-alert
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 아래 내용을 입력하세요:

```env
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx   # Gmail 앱 비밀번호 (16자리)
RECIPIENT_EMAIL=your_email@gmail.com

# 리멤버 로그인 (선택)
NAVER_ID=your_naver_id
NAVER_PASSWORD=your_naver_pw
```

> **Gmail 앱 비밀번호 발급**: Google 계정 → 보안 → 2단계 인증 활성화 → 앱 비밀번호 생성

### 3. 로컬 테스트 실행

```bash
# 이메일 발송 없이 콘솔 미리보기
python main.py --dry-run

# 특정 플랫폼만 테스트 (리멤버 Playwright 제외)
python main.py --skip-playwright

# DB 기록 없이 테스트 (중복 방지 비활성)
python main.py --dry-run --no-mark
```

---

## ⚙️ GitHub Actions 자동화

### Secrets 등록

GitHub 리포지토리 → Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 설명 |
|------------|------|
| `GMAIL_USER` | Gmail 주소 |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 |
| `RECIPIENT_EMAIL` | 수신 이메일 |
| `NAVER_ID` | 네이버 ID (리멤버용, 선택) |
| `NAVER_PASSWORD` | 네이버 PW (리멤버용, 선택) |

### 실행 스케줄

- 평일(월~금) 오전 8시 KST 자동 실행
- GitHub Actions 페이지에서 수동 실행 가능 (workflow_dispatch)

---

## 🔍 키워드 필터링

### 포함 키워드 (점수 상승)

| 키워드 | 가중치 |
|--------|--------|
| Agent, 에이전트 | +2점 |
| LLM, RAG | +2점 |
| LLM + RAG 동시 | +3점 보너스 |
| 자동화, 챗봇, AI 등 | +1점 |

### 제외 키워드 (즉시 제거)

네트워크, 보안, 임베디드, 백엔드, 프론트엔드, DevOps, AWS, MLOps, QA, UI/UX 등

`core/config.py`에서 키워드를 자유롭게 수정할 수 있습니다.

---

## 📧 이메일 형식

```
예슬님, 오늘(2024년 01월 15일) 맞춤 채용 공고 12건을 끓여왔습니다! 🥣✨

📬 오늘의 맞춤 채용 공고
─────────────────────────────────────────────

1. ⭐⭐⭐ [원티드] 카카오
   📌 직무     : LLM 기반 대화 AI 엔지니어
   💰 연봉     : 7,000~9,000만원
   🏢 기업규모  : 대기업
   📍 근무지   : 서울 강남구
   ⏰ 마감기한 : 2024-02-15
   📊 기업평점 : 4.2
   🔗 공고링크 : https://...
```

---

## 🛠️ 기술 스택

| 항목 | 기술 |
|------|------|
| 언어 | Python 3.11+ |
| 크롤링 | requests, BeautifulSoup4, Playwright |
| RSS | feedparser |
| OCR | pytesseract + Pillow |
| 중복 방지 | SQLite |
| 이메일 | smtplib + Gmail SMTP |
| 스케줄러 | GitHub Actions cron |
| 환경 변수 | python-dotenv |
