# Docker 환경

## 구성

```
docker/
├── Dockerfile           # 앱 이미지 빌드
├── docker-compose.yml   # 전체 서비스 구성
└── readme.md
```

## 서비스

| 서비스 | 이미지 | 포트 | 설명 |
|--------|--------|------|------|
| postgres | postgres:16-alpine | 5432 | PostgreSQL DB |
| app | (빌드) | 8000 | FastAPI 앱 |

## 실행 방법

### 전체 실행 (DB + 앱)

```bash
cd docker
docker-compose up -d
```

### DB만 실행 (로컬 개발용)

```bash
cd docker
docker-compose up -d postgres

# 앱은 로컬에서 실행
cd ..
uvicorn app.main:app --reload
```

### 로그 확인

```bash
docker-compose logs -f app      # 앱 로그
docker-compose logs -f postgres # DB 로그
```

### 종료

```bash
docker-compose down        # 컨테이너 종료
docker-compose down -v     # 컨테이너 + 볼륨 삭제 (DB 데이터 삭제)
```

## 환경변수

docker-compose는 프로젝트 루트의 `.env` 파일을 자동으로 읽습니다.

```env
# .env
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

### DB 접속 정보

| 환경 | 호스트 | 포트 | DB | 유저 | 비밀번호 |
|------|--------|------|-----|------|----------|
| Docker 내부 | postgres | 5432 | dev_db | dev | dev1234 |
| 로컬 | localhost | 5432 | dev_db | dev | dev1234 |

## 개발 모드

`docker-compose.yml`에서 볼륨 마운트로 핫 리로드 지원:

```yaml
volumes:
  - ../app:/app/app
  - ../core:/app/core
command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

코드 수정하면 자동으로 서버 재시작됩니다.

## DB 접속 (psql)

```bash
# 컨테이너 내부에서
docker exec -it together-postgres psql -U dev -d dev_db

# 또는 로컬에서 (psql 설치 필요)
psql -h localhost -U dev -d dev_db
```

## 이미지 재빌드

```bash
docker-compose build --no-cache
docker-compose up -d
```
