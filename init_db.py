#!/usr/bin/env python3
"""데이터베이스 초기화 스크립트"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from fastapi_app.db.session import engine
from fastapi_app.db.base import Base

def init_db():
    """데이터베이스 테이블 생성"""
    print("🔨 데이터베이스 테이블 생성 중...")
    Base.metadata.create_all(bind=engine)
    print("✅ 데이터베이스 테이블 생성 완료!")

if __name__ == "__main__":
    init_db()
