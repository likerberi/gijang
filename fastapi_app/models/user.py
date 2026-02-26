from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.session import Base


class User(Base):
    """사용자 모델"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="generated_by_user", foreign_keys="Report.generated_by")
    merge_projects = relationship("MergeProject", back_populates="user", cascade="all, delete-orphan")
    mapping_templates = relationship("ColumnMappingTemplate", back_populates="user", cascade="all, delete-orphan")
