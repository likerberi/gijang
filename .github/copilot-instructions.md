# Django REST Framework 문서 처리 자동화 API

## 프로젝트 개요
엑셀, 이미지, PDF 파일을 업로드하여 핵심 정보를 추출하고 구조화된 리포트를 생성하는 내부 API 서비스

## 주요 기능
- 파일 업로드 (Excel, 이미지, PDF)
- 사용자 인증 및 권한 관리
- Celery 백그라운드 태스크 처리
- 문서 정보 추출 및 구조화된 리포트 생성
- **다중 엑셀 파일 병합** (열 매핑, 헤더 탐지, 날짜/숫자 정규화)

## 기술 스택
- Django REST Framework
- Celery
- Redis
- PostgreSQL (개발 시 SQLite3)
- Python 3.9+

## 프로젝트 구조
- `config/` - 프로젝트 설정 및 Celery 구성
- `users/` - 사용자 인증 및 관리
- `documents/` - 문서 업로드, 처리, 리포트 생성
- `documents/utils/` - 데이터 정규화 유틸리티 (날짜, 숫자, 헤더 탐지, 열 매핑)
- `fastapi_app/` - FastAPI 버전 API

## 진행 상황
- [x] copilot-instructions.md 파일 생성
- [x] Django 프로젝트 스캐폴딩
- [x] 앱 구조 생성 (users, documents)
- [x] Celery 설정
- [x] 사용자 인증 구현 (JWT)
- [x] 파일 업로드 모델 및 API 구현
- [x] 문서 처리 태스크 구현 (Excel, PDF, 이미지)
- [x] 리포트 생성 기능
- [x] 의존성 설치 및 마이그레이션
- [x] README.md 작성
- [x] 다중 엑셀 병합 기능 구현 (모델, 유틸리티, API, Celery 태스크)
- [x] 열 매핑 / 헤더 탐지 / 날짜·숫자 정규화 유틸리티
- [x] 매핑 템플릿 재사용 기능
- [x] FastAPI 측 병합 API 추가

## 실행 방법

### 기본 실행
```bash
# 가상 환경 활성화
source venv/bin/activate

# Django 서버 실행
python manage.py runserver
```

### Celery 실행 (별도 터미널)
```bash
# Redis 실행 (필요 시)
redis-server

# Celery worker 실행
celery -A config worker --loglevel=info
```

### 관리자 생성
```bash
python manage.py createsuperuser
```

## API 엔드포인트
- `/api/docs/` - Swagger UI API 문서
- `/api/users/register/` - 사용자 등록
- `/api/users/login/` - 로그인
- `/api/documents/documents/` - 문서 업로드 및 관리
- `/api/documents/merge-projects/` - 파일 병합 프로젝트 관리
- `/api/documents/mapping-templates/` - 매핑 템플릿 관리
- `/admin/` - Django 관리자 페이지

## 개발 노트
- 개발 환경에서는 SQLite3 사용 (PostgreSQL 설정 주석 처리됨)
- Celery는 Redis를 브로커로 사용
- JWT 토큰 기반 인증
- 파일은 `media/documents/` 에 저장됨
