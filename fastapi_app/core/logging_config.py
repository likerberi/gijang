"""로깅 설정"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from .config import settings


def setup_logging():
    """로깅 설정 초기화"""
    
    # 로그 디렉토리 생성
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 로그 포맷
    log_format = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    detailed_format = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 루트 로거
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)
    
    # 파일 핸들러 - 일반 로그 (일별 로테이션)
    file_handler = TimedRotatingFileHandler(
        filename=log_dir / "app.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_format)
    root_logger.addHandler(file_handler)
    
    # 파일 핸들러 - 에러 로그 (크기 기반 로테이션)
    error_handler = RotatingFileHandler(
        filename=log_dir / "error.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_format)
    root_logger.addHandler(error_handler)
    
    # Celery 로거
    celery_logger = logging.getLogger("celery")
    celery_handler = TimedRotatingFileHandler(
        filename=log_dir / "celery.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    celery_handler.setFormatter(detailed_format)
    celery_logger.addHandler(celery_handler)
    
    # SQLAlchemy 로거 (프로덕션에서는 WARNING만)
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.setLevel(logging.WARNING if not settings.DEBUG else logging.INFO)
    
    # Uvicorn 로거
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers = []  # 기본 핸들러 제거
    access_handler = TimedRotatingFileHandler(
        filename=log_dir / "access.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    access_handler.setFormatter(log_format)
    uvicorn_access.addHandler(access_handler)
    
    logging.info("로깅 시스템 초기화 완료")
    logging.info(f"로그 디렉토리: {log_dir.absolute()}")
    

def get_logger(name: str) -> logging.Logger:
    """모듈별 로거 가져오기"""
    return logging.getLogger(name)
