from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.session import Base
from ..schemas.document import FileType, DocumentStatus
import enum


class Document(Base):
    """문서 모델"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(SQLEnum(FileType), nullable=False)
    file_size = Column(Integer, default=0)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 관계
    user = relationship("User", back_populates="documents")
    extracted_data = relationship("ExtractedData", back_populates="document", uselist=False, cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="document", cascade="all, delete-orphan")


class ExtractedData(Base):
    """추출된 데이터 모델"""
    __tablename__ = "extracted_data"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), unique=True, nullable=False)
    extracted_text = Column(Text, default="")
    meta_info = Column(JSON, default=dict)  # metadata -> meta_info로 변경
    structured_data = Column(JSON, default=dict)
    total_pages = Column(Integer, default=0)
    total_rows = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    document = relationship("Document", back_populates="extracted_data")


class Report(Base):
    """리포트 모델"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    content = Column(JSON, default=dict)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    document = relationship("Document", back_populates="reports")
    generated_by_user = relationship("User", back_populates="reports", foreign_keys=[generated_by])


class MergeProject(Base):
    """파일 병합 프로젝트 모델"""
    __tablename__ = "merge_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(String(20), default="draft")  # draft, analyzing, ready, merging, completed, failed
    
    column_mapping = Column(JSON, default=dict)
    date_columns = Column(JSON, default=list)
    number_columns = Column(JSON, default=list)
    date_output_format = Column(String(50), default="%Y-%m-%d")
    
    analysis_result = Column(JSON, default=dict)
    merged_file_path = Column(String(500), nullable=True)
    merge_log = Column(JSON, default=dict)
    
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 관계
    user = relationship("User", back_populates="merge_projects")
    files = relationship("MergeFile", back_populates="project", cascade="all, delete-orphan")


class MergeFile(Base):
    """병합 대상 파일 모델"""
    __tablename__ = "merge_files"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("merge_projects.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, default=0)
    
    detected_headers = Column(JSON, default=list)
    header_row_index = Column(Integer, default=0)
    total_rows = Column(Integer, default=0)
    column_types = Column(JSON, default=dict)
    sample_data = Column(JSON, default=list)
    
    is_analyzed = Column(Integer, default=0)  # SQLite boolean
    is_processed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    project = relationship("MergeProject", back_populates="files")


class ColumnMappingTemplate(Base):
    """매핑 템플릿 모델"""
    __tablename__ = "column_mapping_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    
    column_mapping = Column(JSON, default=dict)
    date_columns = Column(JSON, default=list)
    number_columns = Column(JSON, default=list)
    date_output_format = Column(String(50), default="%Y-%m-%d")
    custom_aliases = Column(JSON, default=dict)
    is_public = Column(Integer, default=0)  # SQLite boolean
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    user = relationship("User", back_populates="mapping_templates")
