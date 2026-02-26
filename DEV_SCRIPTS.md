# 개발 스크립트 사용법

## 빠른 시작

### 모든 서비스 한 번에 시작

```bash
# 기본 (FastAPI + Celery)
./start_dev.sh

# Flower 포함
./start_dev.sh --with-flower
```

### 서비스 관리

```bash
# 종료
./stop_dev.sh

# 재시작
./restart_dev.sh

# 실시간 로그 확인
./logs_dev.sh
```

## 스크립트 설명

### start_dev.sh
개발 환경의 모든 서비스를 백그라운드로 시작합니다.

**동작:**
1. 기존 프로세스 정리
2. Redis 확인 및 시작
3. 데이터베이스 초기화 (최초 1회)
4. FastAPI 서버 시작 (포트 8001)
5. Celery Worker 시작
6. Flower 시작 (--with-flower 옵션 시)

**로그 파일:**
- `logs/fastapi.log` - FastAPI 서버
- `logs/celery.log` - Celery Worker
- `logs/flower.log` - Flower (옵션)

**PID 파일:**
- `.fastapi.pid`
- `.celery.pid`
- `.flower.pid`

### stop_dev.sh
모든 개발 서비스를 안전하게 종료합니다.

### restart_dev.sh
서비스를 재시작합니다. 코드 변경 후 전체 재시작이 필요할 때 사용하세요.

참고: FastAPI는 `--reload` 옵션으로 실행되므로 코드 변경 시 자동으로 재시작됩니다.

### logs_dev.sh
모든 서비스의 로그를 컬러로 실시간 출력합니다.

- 🟢 녹색: FastAPI 로그
- 🟡 노란색: Celery 로그
- 🟣 보라색: Flower 로그
- 🔴 빨간색: ERROR 메시지

## 개발 워크플로우

### 1. 처음 시작

```bash
# 의존성 설치
source venv/bin/activate
pip install -r requirements-fastapi.txt

# 서비스 시작
./start_dev.sh --with-flower
```

### 2. 일상적인 개발

```bash
# 아침에 시작
./start_dev.sh

# 코딩...
# (FastAPI 코드는 자동으로 재시작됨)

# 로그 확인
./logs_dev.sh

# 저녁에 종료
./stop_dev.sh
```

### 3. 문제 발생 시

```bash
# 전체 재시작
./restart_dev.sh

# 로그 확인
tail -f logs/fastapi.log  # FastAPI 에러
tail -f logs/celery.log   # Celery 에러
```

## 프로덕션 vs 개발

| 항목 | 개발 (start_dev.sh) | 프로덕션 (start_production.sh) |
|------|---------------------|-------------------------------|
| FastAPI | 1 worker, --reload | 4 workers, no reload |
| Celery | 기본 concurrency | 4 concurrency |
| 로그 | 별도 파일 | 별도 파일 + 로테이션 |
| 자동 재시작 | FastAPI만 | 없음 |
| Flower | 선택사항 | 기본 포함 |

## 트러블슈팅

### 포트가 이미 사용 중

```bash
# 프로세스 확인
lsof -i :8001  # FastAPI
lsof -i :5555  # Flower

# 강제 종료 후 재시작
./stop_dev.sh
./start_dev.sh
```

### 서비스가 시작되지 않음

```bash
# 로그 확인
cat logs/fastapi.log
cat logs/celery.log

# Redis 확인
redis-cli ping

# 수동 실행으로 디버그
python -m uvicorn fastapi_app.main:app --reload --port 8001
```

### PID 파일 문제

```bash
# PID 파일 정리
rm .*.pid

# 다시 시작
./start_dev.sh
```
