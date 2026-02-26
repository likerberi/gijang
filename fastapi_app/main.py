from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import logging

from .api import users, documents, auth, websocket, merge
from .core.config import settings
from .core.logging_config import setup_logging
from .core.exception_handlers import register_exception_handlers
from .db.session import engine
from .db.base import Base

# 로깅 설정
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행"""
    # 시작 시
    logger.info("🚀 FastAPI 애플리케이션 시작")
    logger.info(f"환경: {'개발' if settings.DEBUG else '프로덕션'}")
    logger.info(f"데이터베이스: {settings.DATABASE_URL}")
    yield
    # 종료 시
    logger.info("👋 FastAPI 애플리케이션 종료")


app = FastAPI(
    title="문서 처리 자동화 API",
    description="엑셀, 이미지, PDF 문서 처리 및 정보 추출 API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 예외 핸들러 등록
register_exception_handlers(app)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"CORS 설정: {settings.CORS_ORIGINS}")

# 미디어 파일 서빙
os.makedirs("media", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")


# 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["인증"])
app.include_router(users.router, prefix="/api/users", tags=["사용자"])
app.include_router(documents.router, prefix="/api/documents", tags=["문서"])
app.include_router(merge.router, prefix="/api/merge", tags=["파일 병합"])
app.include_router(websocket.router, tags=["WebSocket"])


@app.get("/", tags=["Root"])
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "문서 처리 자동화 API에 오신 것을 환영합니다 (FastAPI)",
        "version": "2.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "auth": {
                "register": "/api/auth/register",
                "login": "/api/auth/login",
            },
            "users": {
                "me": "/api/users/me",
                "profile": "/api/users/profile",
            },
            "documents": {
                "upload": "/api/documents/upload",
                "list": "/api/documents/",
            },
            "merge": {
                "projects": "/api/merge/",
                "templates": "/api/merge/templates",
            }
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "framework": "FastAPI"}
