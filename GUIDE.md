# 사용 가이드

## 내가 직접 쓰는 파일 (3개)

### 1. `profile/me.md` — 내 정보
처음 한 번 채우고, 변화 있을 때만 업데이트.

```
- 학력
- 기술 스택 (Python, LLM, RAG 등)
- 자기소개 한 문장
- 취업 목표
```

### 2. `cv/experiences.md` — 경험 기록
새 프로젝트/경험 생길 때마다 자유롭게 추가.
완전한 문장 아니어도 됨. 키워드·단편 메모도 OK.

```markdown
## 프로젝트명
- 언제:
- 뭘 했는지:
- 결과/배운 것:
- 기술:
```

### 3. `profile/criteria.yaml` — 회사 기준
원하는 조건이 바뀔 때만 수정.
수정하면 필터가 자동으로 반영됨 (코드 건드릴 필요 없음).

---

## Claude에게 하는 말 (그냥 채팅으로 입력)

> ⚠️ 아래는 슬래시 명령어가 아닙니다. 그냥 Claude한테 말하듯 입력하면 돼요.

| 하고 싶은 것 | Claude한테 이렇게 말하기 |
|-------------|------------------------|
| 기본 자소서 생성 | "자소서 만들어줘" |
| 특정 회사 자소서 | "토스 자소서 만들어줘" |
| 전체 회사 자소서 | "타겟 회사 전체 자소서 만들어줘" |
| 회사 탐색 | "회사 탐색해줘" |
| 기준 업데이트 | "criteria 업데이트해줘 — [변경 내용]" |
| 부트캠프 확인 | "부트캠프/공모전 최신 정보 확인해줘" |
| 프롬프트 저장 | "현재 프롬프트 저장해줘" |

---

## 자소서 파이프라인

```
cv/experiences.md 에 경험 추가
        ↓
/gen cv [회사명]
        ↓
cv/generated/companies/회사명.md 확인
        ↓
지원
```

---

## 전체 폴더 한눈에

```
job-alert/
├── GUIDE.md                  ← 지금 이 파일
├── CLAUDE.md                 ← Claude 자동 로드 (건드리지 않아도 됨)
│
├── profile/                  ← 내가 채우는 컨텍스트 (.gitignore)
│   ├── me.md                 ★ 내 정보
│   ├── criteria.yaml         ★ 회사 기준
│   └── target_companies.yaml   타겟 회사 목록
│
├── cv/                       ← 자소서 파이프라인 (.gitignore)
│   ├── experiences.md        ★ 경험 기록
│   ├── PIPELINE.md             파이프라인 상세 설명
│   └── generated/              자동 생성 자소서
│       └── companies/
│
├── opportunities/            ← 부트캠프·공모전 데이터
│   ├── bootcamps.yaml
│   └── competitions.yaml
│
└── (나머지는 자동 실행 코드)
```

★ = 내가 직접 쓰는 파일

---

## 세션 관리 (터미널)

```bash
# 이름 붙여서 시작 (나중에 찾기 쉬움)
claude -n "자소서 작업"
claude -n "회사 탐색"

# 이전 세션 목록 보고 이어서
claude --resume

# 이전 세션 복사해서 새 방향으로
claude --resume <session-id> --fork-session
```
