# Chef AI

요리 AI 시스템

## 사전 요구사항

- Git
- Docker Desktop (Compose V2 포함)

## 설치 및 실행

### 1. 저장소 클론

```bash
git clone https://github.com/dok9gold/together.git
cd together
```

### 2. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 API 키 설정:

```env
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

### 3. Docker 서비스 실행

```bash
cd docker
docker compose up -d
```

> **Note**: 구버전 Docker는 `docker-compose up -d` 사용

### 4. 접속 확인

- http://localhost:8000

## 로그 확인

```bash
cd docker
docker compose logs -f        # 전체 로그
docker compose logs -f app    # 앱 로그만
```

## 종료

```bash
cd docker
docker compose down        # 컨테이너 종료
docker compose down -v     # 볼륨 포함 삭제 (DB 초기화)
```
