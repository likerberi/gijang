"""
프레임워크 독립 Pydantic 스키마

Django DRF serializer 와 FastAPI 양쪽에서 공유.
비즈니스 로직의 입출력 계약을 여기서 정의하고,
각 프레임워크 어댑터에서 변환하여 사용.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# ─── OCR ───

class OCRResultSchema(BaseModel):
    """OCR 처리 결과"""
    text: str = ''
    engine: str = 'none'
    lang: str = ''
    confidence: float = 0.0
    regions: list[dict[str, Any]] = Field(default_factory=list)


# ─── 문서 처리 ───

class PreprocessingInfo(BaseModel):
    """전처리 파이프라인 메타데이터"""
    header_row_detected: int = 0
    meta_rows: list[list[Any]] = Field(default_factory=list)
    column_mapping: dict[str, Any] = Field(default_factory=dict)
    date_columns: list[str] = Field(default_factory=list)
    number_columns: list[str] = Field(default_factory=list)
    financial_columns: dict[str, Optional[str]] = Field(default_factory=dict)
    sorted_by: Optional[str] = None
    balance_check: Optional[dict[str, Any]] = None
    auto_classifications: dict[str, str] = Field(default_factory=dict)
    rows_before_cleanup: int = 0
    rows_after_cleanup: int = 0
    preprocessing_version: int = 2


class DocumentProcessResult(BaseModel):
    """문서 처리 결과 (process_excel, process_csv, process_image, process_pdf 공통)"""
    extracted_text: str = ''
    structured_data: dict[str, Any] = Field(default_factory=dict)
    total_rows: int = 0
    total_pages: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


# ─── 파일 병합 ───

class FileAnalysis(BaseModel):
    """개별 파일 분석 결과"""
    filename: str
    headers: list[str] = Field(default_factory=list)
    header_row_index: int = 0
    total_rows: int = 0
    column_types: dict[str, str] = Field(default_factory=dict)
    sample_data: list[list[Any]] = Field(default_factory=list)
    error: Optional[str] = None


class MergeAnalysisResult(BaseModel):
    """병합 분석 결과"""
    files: list[FileAnalysis] = Field(default_factory=list)
    suggested_mappings: dict[str, Any] = Field(default_factory=dict)
    all_headers: list[str] = Field(default_factory=list)


# ─── 자동화 ───

class AutomationStepSchema(BaseModel):
    """자동화 스텝 정의"""
    action: str
    selector: str = ''
    value: str = ''
    description: str = ''
    wait_after: int = 500


class AutomationDryRunReport(BaseModel):
    """드라이런 결과"""
    task_name: str
    target_url: str
    date_range: dict[str, str]
    period: str
    total_steps: int
    steps: list[dict[str, Any]]
    download_format: str = ''
    download_selector: str = ''
    validation: dict[str, Any] = Field(default_factory=dict)


# ─── 검색 ───

class SearchResultItem(BaseModel):
    """검색 결과 항목"""
    type: str  # document | extracted | report
    id: int
    title: str
    subtitle: str = ''
    snippet: str = ''
    date: str = ''
    url: str = ''


class SearchResponse(BaseModel):
    """검색 응답"""
    query: str
    total: int
    results: list[SearchResultItem]
