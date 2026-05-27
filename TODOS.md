# TODOS — job-alert

## Phase 2: AI Intelligence 확장 (30일 사용 후 판단)
- [ ] AWS Lambda + EventBridge 스케줄러로 전환 (GitHub Actions 대신)
- [ ] DynamoDB: Discord 반응(읽음/클릭) 추적
- [ ] RAG 개인화: profile/me.md 기반 "이 논문이 내 스킬과 어떻게 연결되나" 쿼리
- [ ] profile/criteria.yaml 기반 AI 취업 직결 일일 액션 아이템 통합

## 기술 부채
- [ ] GitHub Actions: jobs.db cache 전략 → artifact storage로 전환 (cache 미스 위험)
- [ ] `core/enricher.py`: Jobplanet 스크래핑이 에러 시 무언 실패 — 로깅 개선 필요
- [ ] launchd 로컬 스케줄러: data/launchd.out.log 용량 관리 (현재 5MB+)
