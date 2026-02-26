from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    """파일 유형"""
    EXCEL = "excel"
    IMAGE = "image"
    PDF = "pdf"


class DocumentStatus(str, Enum):
    """문서 처리 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# 문서 스키마
class DocumentBase(BaseModel):
    """문서 기본 스키마"""
    file_type: FileType


class DocumentCreate(DocumentBase):
    """문서 생성 스키마"""
    pass


class DocumentResponse(DocumentBase):
    """문서 응답 스키마"""
    id: int
    user_id: int
    original_filename: str
    file_path: str
    file_size: int
    status: DocumentStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DocumentList(BaseModel):
    """문서 목록 응답"""
    total: int
    documents: List[DocumentResponse]


# 추출 데이터 스키마
class ExtractedDataResponse(BaseModel):
    """추출 데이터 응답 스키마"""
    id: int
    document_id: int
    extracted_text: str
    meta_info: Dict[str, Any]  # metadata -> meta_info로 변경
    structured_data: Dict[str, Any]
    total_pages: int
    total_rows: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# 리포트 스키마
class ReportBase(BaseModel):
    """리포트 기본 스키마"""
    title: str = Field(..., min_length=1, max_length=255)
    summary: str


class ReportCreate(ReportBase):
    """리포트 생성 스키마"""
    document_id: int
    content: Dict[str, Any]


class ReportUpdate(BaseModel):
    """리포트 업데이트 스키마"""
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[Dict[str, Any]] = None


class ReportResponse(ReportBase):
    """리포트 응답 스키마"""
    id: int
    document_id: int
    content: Dict[str, Any]
    generated_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 파일 업로드 응답
class UploadResponse(BaseModel):
    """파일 업로드 응답"""
    message: str
    document_id: int
    filename: str
    status: DocumentStatus


# ========================
# 병합 프로젝트 스키마
# ========================

class MergeProjectStatus(str, Enum):
    """병합 프로젝트 상태"""
    DRAFT = "draft"
    ANALYZING = "analyzing"
    READY = "ready"
    MERGING = "merging"
    COMPLETED = "completed"
    FAILED = "failed"


class MergeFileResponse(BaseModel):
    """병합 파일 응답"""
    id: int
    project_id: int
    original_filename: str
    file_size: int
    detected_headers: List[str] = []
    header_row_index: int = 0
    total_rows: int = 0
    column_types: Dict[str, str] = {}
    sample_data: List[List[Any]] = []
    is_analyzed: bool = False
    is_processed: bool = False
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class MergeProjectCreate(BaseModel):
    """병합 프로젝트 생성"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""


class MergeProjectResponse(BaseModel):
    """병합 프로젝트 응답"""
    id: int
    user_id: int
    name: str
    description: str
    status: str
    column_mapping: Dict[str, str] = {}
    date_columns: List[str] = []
    number_columns: List[str] = []
    date_output_format: str = "%Y-%m-%d"
    analysis_result: Dict[str, Any] = {}
    merged_file_path: Optional[str] = None
    merge_log: Dict[str, Any] = {}
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    files: List[MergeFileResponse] = []
    
    class Config:
        from_attributes = True


class MergeProjectList(BaseModel):
    """병합 프로젝트 목록"""
    total: int
    projects: List[MergeProjectResponse]


class UpdateMappingRequest(BaseModel):
    """매핑 규칙 업데이트 요청"""
    column_mapping: Optional[Dict[str, str]] = None
    date_columns: Optional[List[str]] = None
    number_columns: Optional[List[str]] = None
    date_output_format: Optional[str] = "%Y-%m-%d"


class MappingTemplateCreate(BaseModel):
    """매핑 템플릿 생성"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    column_mapping: Dict[str, str] = {}
    date_columns: List[str] = []
    number_columns: List[str] = []
    date_output_format: str = "%Y-%m-%d"
    custom_aliases: Dict[str, List[str]] = {}
    is_public: bool = False


class MappingTemplateResponse(BaseModel):
    """매핑 템플릿 응답"""
    id: int
    user_id: int
    name: str
    description: str
    column_mapping: Dict[str, str] = {}
    date_columns: List[str] = []
    number_columns: List[str] = []
    date_output_format: str
    custom_aliases: Dict[str, List[str]] = {}
    is_public: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
