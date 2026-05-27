# Job Alert — Docker 사용법

이 프로젝트는 Docker를 사용하여 환경설정(Python, Tesseract OCR, Playwright Chromium 등)을 컨테이너 내부로 표준화하고, 로컬 환경의 번거로운 의존성 설치 과정 없이 실행할 수 있도록 구성되어 있습니다.

---

## 🏗️ Docker 및 환경 구성 개요

Apple Silicon(M1/M2/M3) 환경의 macOS를 위해 **Colima**와 **Docker CLI**를 기반으로 경량 가상 머신(VM) 및 컨테이너 런타임 환경을 구축했습니다.

### 설치 및 구성된 내역
1. **Colima**: Docker Desktop 없이 터미널을 통해 Docker 컨테이너를 구동할 수 있는 초경량 오픈소스 가상 머신(Apple Silicon 지원).
2. **Docker & Docker Compose CLI**: Docker 및 docker-compose 명령어 도구.
3. **`~/.docker/config.json`**: 최신 `docker compose` 명령어가 CLI 플러그인을 자동으로 찾아 실행할 수 있도록 설정 적용.
4. **`~/.zshrc` PATH 설정**: `brew`, `colima`, `docker` 명령어를 어느 터미널 탭에서나 바로 실행할 수 있도록 Homebrew PATH 설정을 추가 완료했습니다.

---

## 🚀 사용법 및 주요 명령어

### 1. Colima 실행 (Docker Daemon 켜기)
터미널을 열고 Docker를 구동하려면 아래 명령어로 Colima를 실행합니다. (Mac 부팅 후 최초 1회 실행 필요)
```bash
colima start
```

> [!NOTE]
> Colima VM이 켜진 후에는 `docker ps` 등 기존 Docker 명령어를 그대로 사용할 수 있습니다.

### 2. 컨테이너 빌드
코드나 `requirements.txt`에 변경이 있을 경우 Docker 이미지를 다시 빌드합니다.
```bash
docker compose build
```

### 3. 드라이 런 (이메일 발송 없이 수집/분석 테스트)
수집, 필터링, AI 요약 및 자소서 작성이 정상적으로 작동하는지 콘솔창에서 테스트합니다.
```bash
docker compose run --rm job-alert
```
*실행 명령어는 기본적으로 `docker-compose.yml`의 `command: python main.py --dry-run`에 의해 드라이 런으로 작동합니다.*

### 4. 실제 실행 (수집 후 이메일 및 디스코드 발송)
실제 수집 결과를 이메일로 전송하고 이력을 DB에 저장하려면 아래 명령어를 실행합니다.
```bash
docker compose run --rm job-alert python main.py
```

### 5. Colima 종료 (Docker Daemon 끄기)
가상 머신 실행을 중단하여 로컬 CPU 및 메모리 자원을 환수합니다.
```bash
colima stop
```

---

## 💾 볼륨 및 상태 보존 (Volume Mount)

`docker-compose.yml` 파일에서 볼륨 마운트가 아래와 같이 구성되어 있습니다:
```yaml
volumes:
  - .:/app
```
컨테이너 내부와 현재 로컬 작업 폴더(`/Users/gayeseul/Desktop/dev/job-alert`)가 실시간으로 연결됩니다. 따라서:
* 수집 진행 시 컨테이너 내부에서 기록된 **`jobs.db` SQLite 파일이 로컬 폴더에 바로 보존**됩니다.
* 코드 수정이나 YAML 파일(`profile/criteria.yaml` 등)을 수정할 경우 이미지를 다시 빌드하지 않아도 **컨테이너 실행 시 즉시 반영**됩니다.
* 로컬의 `.venv`, `__pycache__` 등은 `.dockerignore`를 통해 빌드 시 제외되어 안전합니다.
