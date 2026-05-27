# 자소서 파이프라인 사용법

## 전체 흐름

```text
contents/experiences.md (내가 자유롭게 경험 나열)
        ↓
    /gen cv
        ↓
outputs/cv/generated/base_coverletter.md (기본 자소서 — STAR 형식 정제)
        ↓
    /gen cv [회사명]
        ↓
outputs/cv/generated/companies/[회사명].md (회사 맞춤 자소서)
```

---

## 명령어

### 기본 자소서 생성
```bash
/gen cv
```
- `contents/experiences.md`를 읽어 STAR 형식으로 정제
- `outputs/cv/generated/base_coverletter.md` 저장

### 회사별 맞춤 자소서 생성
```bash
/gen cv 토스
/gen cv 뤼튼
/gen cv 카카오
```
- 해당 회사의 공식 채용 페이지 JD(Job Description)를 참고
- `config/criteria.yaml`의 회사 정보 활용
- `outputs/cv/generated/companies/토스.md` 저장

### 모든 타겟 회사 일괄 생성
```bash
/gen cv --all
```
- `config/target_companies.yaml`의 모든 회사에 대해 자소서 생성

---

## 자소서 항목 구조 (자동 생성 형식)

각 회사별 자소서는 아래 항목으로 구성됩니다:

1. **지원 동기** (회사 특성 반영)
2. **핵심 경험** (STAR 형식: Situation → Task → Action → Result)
3. **기술 역량** (JD 키워드 매핑)
4. **입사 후 목표** (회사 비전과 연결)

---

## 팁

- `contents/experiences.md`에 경험을 추가할 때마다 `/gen cv` 재실행
- 회사별 자소서는 JD가 업데이트될 때 재생성 권장
- 최종 지원 전 `/gen cv [회사명] --review` 로 품질 검수 요청 가능
