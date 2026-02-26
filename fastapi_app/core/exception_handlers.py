"""전역 예외 핸들러"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from jose import JWTError
import logging

from ..schemas.response import error_response

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """입력 검증 오류 핸들러"""
    logger.warning(f"입력 검증 실패: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            message="입력 데이터가 올바르지 않습니다",
            error_code="VALIDATION_ERROR",
            details=exc.errors()
        )
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """데이터베이스 오류 핸들러"""
    logger.error(f"데이터베이스 오류: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            message="데이터베이스 처리 중 오류가 발생했습니다",
            error_code="DATABASE_ERROR"
        )
    )


async def jwt_exception_handler(request: Request, exc: JWTError):
    """JWT 오류 핸들러"""
    logger.warning(f"JWT 오류: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error_response(
            message="인증 토큰이 유효하지 않습니다",
            error_code="INVALID_TOKEN"
        ),
        headers={"WWW-Authenticate": "Bearer"}
    )


async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러"""
    logger.error(f"처리되지 않은 예외: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            message="서버 내부 오류가 발생했습니다",
            error_code="INTERNAL_ERROR"
        )
    )


def register_exception_handlers(app):
    """예외 핸들러 등록"""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(JWTError, jwt_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("전역 예외 핸들러 등록 완료")
