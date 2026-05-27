# Job Alert — Claude 하네스

이 파일은 Claude Code가 이 프로젝트를 열 때 **자동으로 읽는** 유일한 진입점입니다.
여기 적힌 내용이 이 프로젝트에서 Claude의 행동 기준이 됩니다.

---

## 작업 전 필수 독해 (명령 실행 전 항상)

| 파일 | 목적 |
|------|------|
| `GUIDE.md` | 사용 가이드 (파일 구조·명령어 전체 정리) |
| `profile/me.md` | 예슬의 배경·기술·목표 |
| `profile/criteria.yaml` | 회사·직무 선정 기준 (**코드 설정의 소스**) |
| `profile/target_companies.yaml` | 타겟 회사 + 공식 채용 URL |
| `cv/experiences.md` | 날 경험 목록 (자소서 소스) |

---

## 목표

**예슬을 취업시키는 것.** 모든 작업의 최우선 기준.

---

## 폴더 구조

```
job-alert/
├── CLAUDE.md                       ← 진입점 (지금 이 파일)
│
├── profile/                        ← 고정 컨텍스트 (Claude가 항상 읽음)
│   ├── me.md                       ← 사용자 배경/기술/목표
│   ├── criteria.yaml               ← 회사·직무 기준 (core/config.py의 소스)
│   └── target_companies.yaml       ← 타겟 회사 + 공식 채용 URL
│
├── cv/                             ← 자소서 파이프라인
│   ├── experiences.md              ← 날 경험 (여기만 채우면 됨)
│   ├── PIPELINE.md                 ← 파이프라인 사용법
│   └── generated/                  ← 자동 생성 결과 (.gitignore)
│       └── companies/
│
├── prompts/                        ← 명령 실행 시 로드되는 템플릿
│   ├── company_search.md           ← /search companies 실행 시 읽음
│   ├── cover_letter.md             ← /gen cv 실행 시 읽음
│   └── archive/                    ← /fork prompt 저장소 (.gitignore)
│
├── opportunities/                  ← 부트캠프/공모전 데이터 (YAML만)
│   ├── bootcamps.yaml
│   └── competitions.yaml
│
├── core/                           ← 실행 코드
│   ├── config.py                   ← criteria.yaml 읽어서 설정 생성
│   ├── db.py
│   ├── filter.py
│   ├── mailer.py
│   ├── text_cleaner.py
│   └── opportunities.py            ← 부트캠프/공모전 수집기
│
├── scrapers/                       ← 플랫폼별 스크래퍼
│   ├── saramin.py
│   ├── jobkorea.py
│   ├── programmers.py
│   ├── linkedin.py
│   ├── wanted.py
│   ├── remember.py
│   └── rocketpunch.py
│
├── tests/
│   └── test_e2e.py
└── main.py                         ← 진입점 (CI + launchd 모두 여기)
```

---

## 트리거 키워드 (사용자가 채팅으로 입력하면 수행)

> 슬래시 명령어가 아님. 사용자가 아래 의도로 말하면 해당 동작 수행.

### "현재 프롬프트 저장해줘" (fork prompt)
현재 세션 컨텍스트를 스냅샷으로 저장.
- 저장 위치: `prompts/archive/fork_YYYYMMDD_HHMMSS.md`
- 최신본: `prompts/archive/latest.md`

### "criteria 업데이트해줘"
`profile/criteria.yaml` 수정 → `core/config.py`는 자동 반영 (런타임에 yaml을 직접 읽음).

### "회사 탐색해줘"
1. `prompts/company_search.md` 읽기
2. `profile/criteria.yaml` 기준으로 회사 탐색
3. `profile/target_companies.yaml`의 `careers_url`을 **직접 방문**해 현재 공고 확인
4. 결과를 `target_companies.yaml`에 업데이트

### "자소서 만들어줘 [회사명]"
1. `prompts/cover_letter.md` 읽기
2. `cv/experiences.md` 소스로 사용 (지어내지 말 것)
3. 회사명 없으면 → `cv/generated/base_coverletter.md`
4. 회사명 있으면 → `cv/generated/companies/[회사명].md`

### "부트캠프/공모전 확인해줘"
`core/opportunities.py` 실행 → 부트캠프/공모전 최신 정보 출력.
커널아카데미(⭐ 중요), 패스트캠퍼스 우선 확인.

---

## 불변 규칙

1. **criteria.yaml이 config.py보다 우선** — 필터 기준 변경 시 yaml만 수정
2. **자소서는 experiences.md 기반만** — 없는 경험 지어내지 말 것
3. **채용 공고 = 공식 홈피 직접 확인** — 플랫폼에 없는 공고가 반드시 있음
4. **부트캠프/공모전 추천 = 비용·상금·기간·자격 필수 포함**
5. **알체라는 LLM/자동화 포지션만** — AI 비전(이미지처리) 직무는 필터 대상

---

## 설정 흐름

```
profile/criteria.yaml
        ↓ (런타임 로드)
core/config.py
        ↓
core/filter.py  ←  scrapers/*.py
        ↓
main.py → core/mailer.py → 이메일
```
