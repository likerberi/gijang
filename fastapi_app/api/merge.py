"""
FastAPI 파일 병합 API 엔드포인트
"""
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
    MergeProjectCreate, MergeProjectResponse, MergeProjectList,
    MergeFileResponse, UpdateMappingRequest,
    MappingTemplateCreate, MappingTemplateResponse,
)
from ..schemas.response import success_response, error_response
from ..models.user import User
from ..models.document import MergeProject, MergeFile, ColumnMappingTemplate
from ..core.dependencies import get_current_active_user
from ..core.config import settings
from ..tasks.document_tasks import analyze_merge_files_task, execute_merge_task

router = APIRouter()
logger = logging.getLogger(__name__)


def save_merge_file(upload_file: UploadFile) -> tuple[str, str, int]:
    """병합 대상 파일 저장"""
    upload_dir = Path(settings.UPLOAD_DIR) / "merge_sources" / datetime.now().strftime("%Y/%m/%d")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{upload_file.filename}"
    file_path = upload_dir / filename
    
    upload_file.file.seek(0, 2)
    file_size = upload_file.file.tell()
    upload_file.file.seek(0)
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return str(file_path), upload_file.filename, file_size


# ========================
# 병합 프로젝트 엔드포인트
# ========================

@router.post("/", response_model=MergeProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_merge_project(
    data: MergeProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """병합 프로젝트 생성"""
    project = MergeProject(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        status="draft",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/", response_model=MergeProjectList)
async def list_merge_projects(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """병합 프로젝트 목록"""
    query = db.query(MergeProject).filter(MergeProject.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(MergeProject.status == status_filter)
    
    total = query.count()
    projects = query.order_by(MergeProject.created_at.desc()).offset(skip).limit(limit).all()
    
    return {"total": total, "projects": projects}


@router.get("/{project_id}", response_model=MergeProjectResponse)
async def get_merge_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """프로젝트 상세"""
    project = db.query(MergeProject).filter(
        MergeProject.id == project_id,
        MergeProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_merge_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """프로젝트 삭제"""
    project = db.query(MergeProject).filter(
        MergeProject.id == project_id,
        MergeProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    
    # 파일 삭제
    for mf in project.files:
        try:
            if os.path.exists(mf.file_path):
                os.remove(mf.file_path)
        except Exception:
            pass
    
    if project.merged_file_path and os.path.exists(project.merged_file_path):
        try:
            os.remove(project.merged_file_path)
        except Exception:
            pass
    
    db.delete(project)
    db.commit()
    return None


@router.post("/{project_id}/upload-files", status_code=status.HTTP_201_CREATED)
async def upload_merge_files(
    project_id: int,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """파일 업로드"""
    project = db.query(MergeProject).filter(
        MergeProject.id == project_id,
        MergeProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    
    if project.status not in ("draft", "ready", "failed"):
        raise HTTPException(
            status_code=400,
            detail=f"현재 상태({project.status})에서는 파일을 추가할 수 없습니다"
        )
    
    # 확장자 검증
    allowed_ext = {'.xlsx', '.xls'}
    for f in files:
        ext = Path(f.filename).suffix.lower()
        if ext not in allowed_ext:
            raise HTTPException(
                status_code=400,
                detail=f"'{f.filename}': 엑셀 파일만 업로드 가능합니다 (.xlsx, .xls)"
            )
    
    created = []
    for f in files:
        file_path, original_name, file_size = save_merge_file(f)
        merge_file = MergeFile(
            project_id=project.id,
            file_path=file_path,
            original_filename=original_name,
            file_size=file_size,
        )
        db.add(merge_file)
        created.append(merge_file)
    
    if project.status != "draft":
        project.status = "draft"
    
    db.commit()
    
    return success_response(
        data={"uploaded_count": len(created)},
        message=f"{len(created)}개 파일이 업로드되었습니다"
    )


@router.post("/{project_id}/analyze")
async def analyze_merge_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """파일 분석 시작 (1단계)"""
    project = db.query(MergeProject).filter(
        MergeProject.id == project_id,
        MergeProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    
    if not project.files:
        raise HTTPException(status_code=400, detail="분석할 파일이 없습니다")
    
    if project.status == "analyzing":
        raise HTTPException(status_code=400, detail="이미 분석이 진행 중입니다")
    
    project.status = "analyzing"
    db.commit()
    
    analyze_merge_files_task.delay(project.id)
    
    return success_response(
        data={"project_id": project.id},
        message="파일 분석이 시작되었습니다"
    )


@router.put("/{project_id}/mapping")
async def update_mapping(
    project_id: int,
    data: UpdateMappingRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """매핑 규칙 업데이트 (2단계)"""
    project = db.query(MergeProject).filter(
        MergeProject.id == project_id,
        MergeProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    
    if data.column_mapping is not None:
        project.column_mapping = data.column_mapping
    if data.date_columns is not None:
        project.date_columns = data.date_columns
    if data.number_columns is not None:
        project.number_columns = data.number_columns
    if data.date_output_format is not None:
        project.date_output_format = data.date_output_format
    
    project.status = "ready"
    db.commit()
    db.refresh(project)
    
    return success_response(
        data={"project_id": project.id, "status": project.status},
        message="매핑 규칙이 업데이트되었습니다"
    )


@router.post("/{project_id}/execute")
async def execute_merge(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """병합 실행 (3단계)"""
    project = db.query(MergeProject).filter(
        MergeProject.id == project_id,
        MergeProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    
    if project.status not in ("ready", "failed"):
        raise HTTPException(
            status_code=400,
            detail=f"현재 상태({project.status})에서는 병합을 실행할 수 없습니다"
        )
    
    execute_merge_task.delay(project.id)
    
    return success_response(
        data={"project_id": project.id},
        message="병합이 시작되었습니다"
    )


@router.get("/{project_id}/download")
async def download_merged_file(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """병합 결과 다운로드"""
    project = db.query(MergeProject).filter(
        MergeProject.id == project_id,
        MergeProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    
    if not project.merged_file_path or not os.path.exists(project.merged_file_path):
        raise HTTPException(status_code=404, detail="병합 결과 파일이 없습니다")
    
    filename = f"{project.name}_병합결과.xlsx"
    return FileResponse(
        path=project.merged_file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/{project_id}/files", response_model=List[MergeFileResponse])
async def list_project_files(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """프로젝트 파일 목록"""
    project = db.query(MergeProject).filter(
        MergeProject.id == project_id,
        MergeProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    
    return project.files


@router.delete("/{project_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_file(
    project_id: int,
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """프로젝트에서 파일 제거"""
    project = db.query(MergeProject).filter(
        MergeProject.id == project_id,
        MergeProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    
    merge_file = db.query(MergeFile).filter(
        MergeFile.id == file_id,
        MergeFile.project_id == project_id
    ).first()
    
    if not merge_file:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    
    try:
        if os.path.exists(merge_file.file_path):
            os.remove(merge_file.file_path)
    except Exception:
        pass
    
    db.delete(merge_file)
    db.commit()
    return None


# ========================
# 매핑 템플릿 엔드포인트
# ========================

@router.post("/templates", response_model=MappingTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: MappingTemplateCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """매핑 템플릿 생성"""
    template = ColumnMappingTemplate(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        column_mapping=data.column_mapping,
        date_columns=data.date_columns,
        number_columns=data.number_columns,
        date_output_format=data.date_output_format,
        custom_aliases=data.custom_aliases,
        is_public=1 if data.is_public else 0,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/templates", response_model=List[MappingTemplateResponse])
async def list_templates(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """템플릿 목록"""
    from sqlalchemy import or_
    templates = db.query(ColumnMappingTemplate).filter(
        or_(
            ColumnMappingTemplate.user_id == current_user.id,
            ColumnMappingTemplate.is_public == 1
        )
    ).all()
    return templates


@router.post("/{project_id}/apply-template")
async def apply_template_to_project(
    project_id: int,
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """프로젝트에 템플릿 적용"""
    project = db.query(MergeProject).filter(
        MergeProject.id == project_id,
        MergeProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    
    from sqlalchemy import or_
    template = db.query(ColumnMappingTemplate).filter(
        ColumnMappingTemplate.id == template_id,
        or_(
            ColumnMappingTemplate.user_id == current_user.id,
            ColumnMappingTemplate.is_public == 1
        )
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")
    
    project.column_mapping = template.column_mapping
    project.date_columns = template.date_columns
    project.number_columns = template.number_columns
    project.date_output_format = template.date_output_format
    project.status = "ready"
    db.commit()
    
    return success_response(
        data={"project_id": project.id},
        message=f'템플릿 "{template.name}"이(가) 적용되었습니다'
    )


@router.post("/{project_id}/save-as-template", response_model=MappingTemplateResponse)
async def save_project_as_template(
    project_id: int,
    name: str = Form(...),
    description: str = Form(""),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """프로젝트 매핑을 템플릿으로 저장"""
    project = db.query(MergeProject).filter(
        MergeProject.id == project_id,
        MergeProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    
    template = ColumnMappingTemplate(
        user_id=current_user.id,
        name=name,
        description=description,
        column_mapping=project.column_mapping or {},
        date_columns=project.date_columns or [],
        number_columns=project.number_columns or [],
        date_output_format=project.date_output_format,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template
