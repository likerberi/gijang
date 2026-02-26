"""공통 API 응답 스키마"""
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field


DataT = TypeVar('DataT')


class ApiResponse(BaseModel, Generic[DataT]):
    """표준 API 응답"""
    success: bool = Field(..., description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[DataT] = Field(None, description="응답 데이터")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "요청이 성공적으로 처리되었습니다",
                "data": {}
            }
        }


class ErrorResponse(BaseModel):
    """에러 응답"""
    success: bool = Field(False, description="요청 성공 여부")
    message: str = Field(..., description="에러 메시지")
    error_code: Optional[str] = Field(None, description="에러 코드")
    details: Optional[Any] = Field(None, description="상세 에러 정보")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "요청 처리 중 오류가 발생했습니다",
                "error_code": "INVALID_REQUEST",
                "details": None
            }
        }


class PaginatedResponse(BaseModel, Generic[DataT]):
    """페이지네이션 응답"""
    success: bool = Field(True, description="요청 성공 여부")
    message: str = Field("조회 성공", description="응답 메시지")
    data: List[DataT] = Field(..., description="데이터 목록")
    total: int = Field(..., description="전체 데이터 개수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지당 데이터 개수")
    total_pages: int = Field(..., description="전체 페이지 수")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "조회 성공",
                "data": [],
                "total": 100,
                "page": 1,
                "page_size": 10,
                "total_pages": 10
            }
        }


def success_response(data: Any = None, message: str = "성공적으로 처리되었습니다") -> dict:
    """성공 응답 생성"""
    return {
        "success": True,
        "message": message,
        "data": data
    }


def error_response(
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Any] = None
) -> dict:
    """에러 응답 생성"""
    return {
        "success": False,
        "message": message,
        "error_code": error_code,
        "details": details
    }


def paginated_response(
    data: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "조회 성공"
) -> dict:
    """페이지네이션 응답 생성"""
    import math
    return {
        "success": True,
        "message": message,
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if page_size > 0 else 0
    }
