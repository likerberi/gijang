# 문서 처리 자동화 API (DocMerge)

엑셀, 이미지, PDF 파일을 업로드하여 핵심 정보를 추출하고 구조화된 리포트를 생성하는 Django REST Framework 기반 내부 API 서비스입니다.

> 📖 **웹 사용 가이드**: 서버 실행 후 [http://localhost:8000/guide/](http://localhost:8000/guide/) 에서 스크린샷 기반 사용법을 확인할 수 있습니다.

## 주요 기능

- 📤 **파일 업로드**: Excel, 이미지, PDF 파일 업로드 지원
- 🔐 **사용자 인증**: JWT 기반 사용자 인증 및 권한 관리
- ⚙️ **백그라운드 처리**: Celery를 활용한 비동기 문서 처리
- 📊 **정보 추출**: 업로드된 문서에서 핵심 정보 자동 추출
- 📝 **리포트 생성**: 추출된 정보를 기반으로 구조화된 리포트 자동 생성
- 🔗 **다중 엑셀 병합**: 서로 다른 양식의 엑셀 파일을 열 매핑으로 하나로 통합
- 📋 **매핑 템플릿**: 자주 쓰는 열 매핑 규칙을 저장하여 재사용
- 📚 **API 문서**: Swagger UI를 통한 API 문서 자동 생성

## 기술 스택

- **Backend**: Django 4.2, Django REST Framework
- **Task Queue**: Celery 5.3
- **Cache/Broker**: Redis
- **Database**: PostgreSQL (개발 시 SQLite3 사용 가능)
- **Authentication**: JWT (Simple JWT)
- **Documentation**: drf-spectacular (Swagger UI)
- **File Processing**: 
  - Excel: openpyxl
  - PDF: PyPDF2
  - Image: Pillow

## 프로젝트 구조

```
gijang/
├── config/                 # 프로젝트 설정
│   ├── settings.py        # Django 설정
│   ├── urls.py            # 메인 URL 설정
│   ├── celery.py          # Celery 설정
│   ├── frontend_views.py  # 프론트엔드 페이지 뷰
│   └── wsgi.py
├── users/                 # 사용자 관리 앱
│   ├── models.py          # 커스텀 User 모델
│   ├── serializers.py     # 사용자 시리얼라이저
│   ├── views.py           # 사용자 뷰
│   └── urls.py
├── documents/             # 문서 처리 앱
│   ├── models.py          # Document, MergeProject, MergeFile 등
│   ├── views.py           # 문서/병합 뷰셋
│   ├── tasks.py           # Celery 태스크 (분석, 병합)
│   └── utils/             # 유틸리티
│       ├── normalizers.py # 날짜/숫자 정규화
│       ├── header_detector.py  # 헤더 행 자동 탐지
│       ├── column_mapper.py    # 열 이름 자동 매핑
│       └── merge_service.py    # 병합 오케스트레이션
├── templates/             # 프론트엔드 HTML
│   ├── base.html          # 공통 레이아웃 (사이드바)
│   ├── login.html         # 회원가입/로그인
│   ├── dashboard.html     # 대시보드
│   ├── documents.html     # 문서 관리
│   ├── merge.html         # 파일 병합 워크플로우
│   ├── mapping_templates.html  # 매핑 템플릿
│   └── guide.html         # 사용 가이드
├── static/                # 정적 파일
│   ├── css/style.css      # 전체 스타일
│   └── js/
│       ├── api.js         # JWT API 클라이언트
│       └── app.js         # 공통 유틸리티
├── fastapi_app/           # FastAPI 버전 API
├── media/                 # 업로드 파일 저장
├── requirements.txt
└── manage.py
```

## 빠른 시작 (처음 사용하는 경우)

```bash
# 1. 가상 환경 활성화
source venv/bin/activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. DB 마이그레이션
python manage.py migrate

# 4. 서버 실행 (Django + Redis + Celery 일괄)
./start_dev.sh

# 5. 브라우저에서 접속
#    http://localhost:8000/accounts/login/  ← 회원가입/로그인
#    http://localhost:8000/guide/           ← 사용 가이드
```

## 설치 및 실행 (상세)

### 1. 의존성 설치

```bash
# 가상 환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 수정 (데이터베이스, Redis 등 설정)
```

**개발 시 SQLite3 사용하기:**

[config/settings.py](config/settings.py)에서 PostgreSQL 설정을 주석 처리하고 SQLite3 설정을 활성화하세요:

```python
# PostgreSQL (주석 처리)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         ...
#     }
# }

# SQLite3 (활성화)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 3. 데이터베이스 마이그레이션

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. 슈퍼유저 생성

```bash
python manage.py createsuperuser
```

### 5. Redis 실행 (별도 터미널)

```bash
# macOS (Homebrew)
brew services start redis

# 또는 직접 실행
redis-server
```

### 6. Celery Worker 실행 (별도 터미널)

```bash
# 가상 환경 활성화
source venv/bin/activate

# Celery worker 실행
celery -A config worker --loglevel=info
```

### 7. Django 개발 서버 실행

```bash
python manage.py runserver
```

## API 엔드포인트

### 인증

- `POST /api/users/register/` - 사용자 등록
- `POST /api/users/login/` - 로그인 (JWT 토큰 발급)
- `POST /api/users/token/refresh/` - 토큰 갱신
- `GET /api/users/me/` - 현재 사용자 정보
- `GET/PUT /api/users/profile/` - 프로필 조회/수정

### 문서 관리

- `GET /api/documents/documents/` - 문서 목록
- `POST /api/documents/documents/` - 문서 업로드
- `GET /api/documents/documents/{id}/` - 문서 상세
- `DELETE /api/documents/documents/{id}/` - 문서 삭제
- `POST /api/documents/documents/{id}/reprocess/` - 문서 재처리
- `GET /api/documents/documents/{id}/extracted_data/` - 추출된 데이터 조회
- `GET /api/documents/documents/{id}/reports/` - 문서의 리포트 목록

### 추출 데이터

- `GET /api/documents/extracted-data/` - 추출 데이터 목록
- `GET /api/documents/extracted-data/{id}/` - 추출 데이터 상세

### 리포트

- `GET /api/documents/reports/` - 리포트 목록
- `POST /api/documents/reports/` - 리포트 생성
- `GET /api/documents/reports/{id}/` - 리포트 상세
- `PUT /api/documents/reports/{id}/` - 리포트 수정
- `DELETE /api/documents/reports/{id}/` - 리포트 삭제

### 파일 병합

- `GET /api/documents/merge-projects/` - 병합 프로젝트 목록
- `POST /api/documents/merge-projects/` - 프로젝트 생성
- `POST /api/documents/merge-projects/{id}/upload_files/` - 파일 업로드
- `POST /api/documents/merge-projects/{id}/analyze/` - 파일 분석 시작
- `PUT /api/documents/merge-projects/{id}/update_mapping/` - 매핑 설정
- `POST /api/documents/merge-projects/{id}/apply_template/` - 템플릿 적용
- `POST /api/documents/merge-projects/{id}/execute/` - 병합 실행
- `GET /api/documents/merge-projects/{id}/download/` - 결과 다운로드
- `POST /api/documents/merge-projects/{id}/save_as_template/` - 템플릿 저장

### 매핑 템플릿

- `GET /api/documents/mapping-templates/` - 템플릿 목록
- `POST /api/documents/mapping-templates/` - 템플릿 생성
- `GET /api/documents/mapping-templates/{id}/` - 템플릿 상세
- `DELETE /api/documents/mapping-templates/{id}/` - 템플릿 삭제

### 웹 프론트엔드

| 페이지 | URL | 설명 |
|--------|-----|------|
| 로그인/회원가입 | `/accounts/login/` | 인증 |
| 대시보드 | `/app/` | 요약 통계 |
| 문서 관리 | `/app/documents/` | 파일 업로드/조회 |
| 파일 병합 | `/app/merge/` | 병합 워크플로우 |
| 매핑 템플릿 | `/app/templates/` | 재사용 규칙 |
| 사용 가이드 | `/guide/` | 사용법 안내 |

### API 문서

- `GET /api/docs/` - Swagger UI
- `GET /api/schema/` - OpenAPI Schema

## 사용 예시

### 1. 사용자 등록 및 로그인

```bash
# 사용자 등록
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "password_confirm": "testpass123"
  }'

# 로그인
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

### 2. 문서 업로드

```bash
# 파일 업로드 (토큰 필요)
curl -X POST http://localhost:8000/api/documents/documents/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/file.xlsx" \
  -F "file_type=excel"
```

### 3. 문서 상태 확인

```bash
# 문서 목록 조회
curl -X GET http://localhost:8000/api/documents/documents/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 특정 문서 조회
curl -X GET http://localhost:8000/api/documents/documents/{id}/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 워크플로우

1. **사용자 등록/로그인**: JWT 토큰 발급
2. **파일 업로드**: Excel, 이미지, PDF 파일 업로드
3. **자동 처리**: Celery가 백그라운드에서 문서 처리
   - 파일 유형 감지
   - 정보 추출 (텍스트, 데이터, 메타데이터)
   - 구조화된 데이터 생성
4. **리포트 생성**: 추출된 정보를 기반으로 리포트 자동 생성
5. **결과 조회**: API를 통해 처리 결과 및 리포트 조회

## 처리 가능한 파일 형식

### Excel (.xlsx, .xls)
- 시트 데이터 추출
- 헤더/행 분리
- 통계 정보 생성

### PDF
- 텍스트 추출
- 페이지별 분석
- 메타데이터 추출

### 이미지 (.jpg, .jpeg, .png)
- 이미지 정보 추출
- OCR 준비 (pytesseract 추가 시)

## 관리자 페이지

Django 관리자 페이지에서 모든 데이터를 관리할 수 있습니다:

```
http://localhost:8000/admin/
```

- 사용자 관리
- 문서 관리
- 추출 데이터 조회
- 리포트 관리

## 개발 팁

### Celery 모니터링

```bash
# Celery Flower (모니터링 도구)
pip install flower
celery -A config flower
# http://localhost:5555 에서 확인
```

### 로그 확인

Celery worker 터미널에서 실시간 로그를 확인할 수 있습니다.

### 디버깅

문서 처리가 실패한 경우 Document 모델의 `error_message` 필드를 확인하세요.

## 다음 단계

- [ ] OCR 기능 추가 (pytesseract)
- [ ] CSV 파일 지원
- [ ] AI 기반 정보 추출 (OpenAI API 등)
- [ ] 이메일 알림 기능
- [ ] 문서 검색 기능
- [ ] Docker 컨테이너화

## 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.

## 개발 도구

이 프로젝트는 [GitHub Copilot](https://github.com/features/copilot)의 도움을 받아 개발되었습니다.
