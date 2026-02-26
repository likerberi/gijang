from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import shutil
import logging
from pathlib import Path
from ..db.session import get_db
from ..schemas.document import (
    DocumentResponse, DocumentList, UploadResponse,
    ExtractedDataResponse, ReportResponse, ReportCreate,
    FileType, DocumentStatus
)
from ..schemas.response import success_response, error_response, paginated_response
from ..models.user import User
from ..models.document import Document, ExtractedData, Report
from ..core.dependencies import get_current_active_user
from ..core.config import settings
from ..tasks.document_tasks import process_document_task

router = APIRouter()
logger = logging.getLogger(__name__)


def save_upload_file(upload_file: UploadFile, file_type: FileType) -> tuple[str, str]:
    """파일 저장 및 경로 반환"""
    # 디렉토리 생성
    upload_dir = Path(settings.UPLOAD_DIR) / datetime.now().strftime("%Y/%m/%d")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # 파일명 생성 (타임스탬프 추가)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{upload_file.filename}"
    file_path = upload_dir / filename
    
    # 파일 저장
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return str(file_path), upload_file.filename


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    file_type: FileType = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """문서 업로드"""
    # 파일 확장자 검증
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 파일 형식입니다. 허용: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # 파일 크기 검증
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"파일 크기가 너무 큽니다. 최대: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    # 파일 저장
    file_path, original_filename = save_upload_file(file, file_type)
    
    # DB에 문서 정보 저장
    document = Document(
        user_id=current_user.id,
        original_filename=original_filename,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        status=DocumentStatus.PENDING
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Celery 태스크 실행
    process_document_task.delay(document.id)
    
    return {
        "message": "파일이 업로드되었으며 처리가 시작되었습니다",
        "document_id": document.id,
        "filename": original_filename,
        "status": document.status
    }


@router.get("/", response_model=DocumentList)
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[DocumentStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """문서 목록 조회"""
    query = db.query(Document).filter(Document.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(Document.status == status_filter)
    
    total = query.count()
    documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "documents": documents
    }


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """문서 상세 조회"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문서를 찾을 수 없습니다"
        )
    
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """문서 삭제"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문서를 찾을 수 없습니다"
        )
    
    # 파일 삭제
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        print(f"파일 삭제 오류: {e}")
    
    db.delete(document)
    db.commit()
    
    return None


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """문서 재처리"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문서를 찾을 수 없습니다"
        )
    
    if document.status == DocumentStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 처리 중인 문서입니다"
        )
    
    document.status = DocumentStatus.PENDING
    document.error_message = None
    db.commit()
    
    # Celery 태스크 실행
    process_document_task.delay(document.id)
    
    return document


@router.get("/{document_id}/extracted-data", response_model=ExtractedDataResponse)
async def get_extracted_data(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """추출된 데이터 조회"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문서를 찾을 수 없습니다"
        )
    
    if not document.extracted_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="추출된 데이터가 없습니다"
        )
    
    return document.extracted_data


@router.get("/{document_id}/reports", response_model=List[ReportResponse])
async def get_document_reports(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """문서의 리포트 목록"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문서를 찾을 수 없습니다"
        )

    return document.reports


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """원본 파일 다운로드"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        logger.warning(f"문서 다운로드 실패 - 문서 없음: {document_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문서를 찾을 수 없습니다"
        )
    
    if not os.path.exists(document.file_path):
        logger.error(f"문서 파일 없음: {document.file_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없습니다"
        )
    
    logger.info(f"파일 다운로드: {document.original_filename} (user: {current_user.id})")
    
    return FileResponse(
        path=document.file_path,
        filename=document.original_filename,
        media_type="application/octet-stream"
    )


@router.get("/stats/summary")
async def get_document_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """문서 통계"""
    total = db.query(Document).filter(Document.user_id == current_user.id).count()
    pending = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.status == DocumentStatus.PENDING
    ).count()
    processing = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.status == DocumentStatus.PROCESSING
    ).count()
    completed = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.status == DocumentStatus.COMPLETED
    ).count()
    failed = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.status == DocumentStatus.FAILED
    ).count()
    
    return success_response(
        data={
            "total": total,
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed
        },
        message="통계 조회 성공"
    )
