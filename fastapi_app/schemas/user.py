from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# 사용자 스키마
class UserBase(BaseModel):
    """사용자 기본 스키마"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """사용자 생성 스키마"""
    password: str = Field(..., min_length=8, max_length=100)
    phone: Optional[str] = None
    department: Optional[str] = None


class UserLogin(BaseModel):
    """로그인 스키마"""
    username: str
    password: str


class UserResponse(UserBase):
    """사용자 응답 스키마"""
    id: int
    phone: Optional[str] = None
    department: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """사용자 업데이트 스키마"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department: Optional[str] = None


# 토큰 스키마
class Token(BaseModel):
    """토큰 응답 스키마"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """토큰 데이터 스키마"""
    user_id: Optional[int] = None
    username: Optional[str] = None
