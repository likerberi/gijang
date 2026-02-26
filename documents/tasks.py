from celery import shared_task
from django.utils import timezone
from .models import Document, ExtractedData, Report, MergeProject, MergeFile
import logging
import os

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_document(self, document_id):
    """문서 처리 태스크"""
    try:
        document = Document.objects.get(id=document_id)
        document.status = 'processing'
        document.save()
        
        # 파일 유형에 따라 처리
        if document.file_type == 'excel':
            result = process_excel(document)
        elif document.file_type == 'image':
            result = process_image(document)
        elif document.file_type == 'pdf':
            result = process_pdf(document)
        else:
            raise ValueError(f"지원하지 않는 파일 유형: {document.file_type}")
        
        # 추출된 데이터 저장
        ExtractedData.objects.update_or_create(
            document=document,
            defaults=result
        )
        
        # 문서 상태 업데이트
        document.status = 'completed'
        document.processed_at = timezone.now()
        document.save()
        
        # 리포트 생성
        generate_report.delay(document_id)
        
        logger.info(f"문서 처리 완료: {document.original_filename}")
        return {'status': 'success', 'document_id': document_id}
        
    except Document.DoesNotExist:
        logger.error(f"문서를 찾을 수 없습니다: {document_id}")
        raise
    except Exception as e:
        logger.error(f"문서 처리 오류: {str(e)}")
        document.status = 'failed'
        document.error_message = str(e)
        document.save()
        
        # 재시도
        raise self.retry(exc=e, countdown=60)


def process_excel(document):
    """엑셀 파일 처리"""
    try:
        import openpyxl
        
        wb = openpyxl.load_workbook(document.file.path)
        sheet = wb.active
        
        # 데이터 추출
        data = []
        for row in sheet.iter_rows(values_only=True):
            data.append(list(row))
        
        # 헤더와 데이터 분리
        headers = data[0] if data else []
        rows = data[1:] if len(data) > 1 else []
        
        structured_data = {
            'headers': headers,
            'rows': rows,
            'sheet_name': sheet.title,
        }
        
        return {
            'extracted_text': str(data),
            'structured_data': structured_data,
            'total_rows': len(rows),
            'metadata': {
                'sheet_count': len(wb.sheetnames),
                'sheet_names': wb.sheetnames,
            }
        }
    except Exception as e:
        logger.error(f"엑셀 처리 오류: {str(e)}")
        raise


def process_image(document):
    """이미지 파일 처리"""
    try:
        from PIL import Image
        
        img = Image.open(document.file.path)
        
        # 이미지 정보 추출
        metadata = {
            'format': img.format,
            'mode': img.mode,
            'size': img.size,
            'width': img.width,
            'height': img.height,
        }
        
        # OCR이 필요한 경우 여기에 구현
        # pytesseract 등을 사용하여 텍스트 추출
        
        return {
            'extracted_text': '',  # OCR 결과가 들어갈 자리
            'structured_data': {},
            'metadata': metadata,
        }
    except Exception as e:
        logger.error(f"이미지 처리 오류: {str(e)}")
        raise


def process_pdf(document):
    """PDF 파일 처리"""
    try:
        from PyPDF2 import PdfReader
        
        reader = PdfReader(document.file.path)
        
        # 텍스트 추출
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
        
        return {
            'extracted_text': text,
            'structured_data': {},
            'total_pages': len(reader.pages),
            'metadata': {
                'page_count': len(reader.pages),
                'metadata': reader.metadata if reader.metadata else {},
            }
        }
    except Exception as e:
        logger.error(f"PDF 처리 오류: {str(e)}")
        raise


@shared_task
def generate_report(document_id):
    """리포트 생성 태스크"""
    try:
        document = Document.objects.get(id=document_id)
        extracted_data = ExtractedData.objects.get(document=document)
        
        # 리포트 생성 로직
        title = f"{document.original_filename} 분석 리포트"
        
        # 요약 생성
        summary = generate_summary(extracted_data)
        
        # 리포트 내용 생성
        content = {
            'file_info': {
                'filename': document.original_filename,
                'file_type': document.get_file_type_display(),
                'file_size': document.file_size,
                'processed_at': document.processed_at.isoformat() if document.processed_at else None,
            },
            'extracted_data': {
                'total_pages': extracted_data.total_pages,
                'total_rows': extracted_data.total_rows,
                'text_length': len(extracted_data.extracted_text),
            },
            'structured_data': extracted_data.structured_data,
        }
        
        # 리포트 저장
        Report.objects.create(
            document=document,
            title=title,
            summary=summary,
            content=content,
            generated_by=document.user,
        )
        
        logger.info(f"리포트 생성 완료: {document.original_filename}")
        
    except Exception as e:
        logger.error(f"리포트 생성 오류: {str(e)}")
        raise


def generate_summary(extracted_data):
    """요약 생성"""
    summary_parts = []
    
    if extracted_data.total_pages > 0:
        summary_parts.append(f"총 {extracted_data.total_pages}페이지")
    
    if extracted_data.total_rows > 0:
        summary_parts.append(f"총 {extracted_data.total_rows}행의 데이터")
    
    text_length = len(extracted_data.extracted_text)
    if text_length > 0:
        summary_parts.append(f"{text_length:,}자의 텍스트 추출됨")
    
    return ", ".join(summary_parts) if summary_parts else "데이터 추출 완료"


# ========================
# 파일 병합 관련 태스크
# ========================

@shared_task(bind=True, max_retries=2)
def analyze_merge_files(self, project_id):
    """병합 프로젝트의 파일들을 분석하는 태스크 (1단계)"""
    try:
        project = MergeProject.objects.get(id=project_id)
        project.status = 'analyzing'
        project.save()
        
        from .utils.merge_service import MergeService
        service = MergeService()
        
        merge_files = project.files.all()
        file_paths = [mf.file.path for mf in merge_files]
        
        # 전체 분석
        analysis = service.analyze_files(file_paths)
        
        # 개별 파일 분석 결과 저장
        for file_info in analysis.get('files', []):
            try:
                info_filename = file_info.get('filename', '')
                # 파일 경로 기반으로 매칭 (업로드 시 파일명이 변경될 수 있음)
                merge_file = None
                for mf in merge_files:
                    basename = os.path.basename(mf.file.path)
                    if basename == info_filename or mf.original_filename == info_filename:
                        merge_file = mf
                        break
                
                if merge_file is None:
                    logger.warning(f"병합 파일을 찾을 수 없음: {info_filename}")
                    continue
                
                if 'error' not in file_info:
                    merge_file.detected_headers = file_info.get('headers', [])
                    merge_file.header_row_index = file_info.get('header_row_index', 0)
                    merge_file.total_rows = file_info.get('total_rows', 0)
                    merge_file.column_types = file_info.get('column_types', {})
                    merge_file.sample_data = file_info.get('sample_data', [])
                    merge_file.is_analyzed = True
                else:
                    merge_file.error_message = file_info['error']
                merge_file.save()
            except Exception as exc:
                logger.warning(f"병합 파일 처리 오류: {file_info.get('filename')}: {exc}")
        
        # 프로젝트에 분석 결과 저장
        project.analysis_result = {
            'suggested_mappings': analysis.get('suggested_mappings', {}),
            'all_headers': analysis.get('all_headers', []),
            'analyzed_at': timezone.now().isoformat(),
            'files_analyzed': len([f for f in analysis.get('files', []) if 'error' not in f]),
            'files_failed': len([f for f in analysis.get('files', []) if 'error' in f]),
        }
        project.status = 'ready'
        project.save()
        
        logger.info(f"병합 프로젝트 분석 완료: {project.name} ({len(file_paths)}개 파일)")
        return {'status': 'success', 'project_id': project_id}
        
    except MergeProject.DoesNotExist:
        logger.error(f"병합 프로젝트를 찾을 수 없음: {project_id}")
        raise
    except Exception as e:
        logger.error(f"병합 분석 오류: {str(e)}")
        try:
            project.status = 'failed'
            project.error_message = str(e)
            project.save()
        except Exception:
            pass
        raise self.retry(exc=e, countdown=30)


@shared_task(bind=True, max_retries=2)
def execute_merge(self, project_id):
    """병합 실행 태스크 (2단계)"""
    try:
        project = MergeProject.objects.get(id=project_id)
        
        if project.status not in ('ready', 'failed'):
            logger.warning(f"병합 프로젝트 상태가 올바르지 않음: {project.status}")
            return {'status': 'skipped', 'reason': f'status={project.status}'}
        
        project.status = 'merging'
        project.error_message = ''
        project.save()
        
        from .utils.merge_service import MergeService
        from .utils.normalizers import DateNormalizer
        service = MergeService()
        
        # 날짜 포맷 설정
        if project.date_output_format:
            service.date_normalizer = DateNormalizer(output_format=project.date_output_format)
        
        # 커스텀 매핑이 있으면 적용
        if project.column_mapping:
            for original, standard in project.column_mapping.items():
                service.column_mapper.add_mapping(standard, [original])
        
        merge_files = project.files.all()
        file_paths = [mf.file.path for mf in merge_files]
        
        # 병합 실행
        from django.conf import settings as django_settings
        output_dir = os.path.join(
            str(django_settings.MEDIA_ROOT), 'merged',
            timezone.now().strftime('%Y/%m/%d')
        )
        os.makedirs(output_dir, exist_ok=True)
        
        output_filename = f'merged_{project.id}_{timezone.now().strftime("%H%M%S")}.xlsx'
        output_path = os.path.join(output_dir, output_filename)
        
        result = service.merge_files(
            file_paths=file_paths,
            column_mapping=project.column_mapping or {},
            date_columns=project.date_columns or [],
            number_columns=project.number_columns or [],
            output_path=output_path,
            add_source_column=True,
        )
        
        if result['success']:
            # 병합 파일 경로를 Django FileField 상대 경로로 변환
            relative_path = os.path.relpath(output_path, str(django_settings.MEDIA_ROOT))
            project.merged_file = relative_path
            project.merge_log = result
            project.status = 'completed'
            project.completed_at = timezone.now()
            
            # 개별 파일 상태 업데이트
            for log_entry in result.get('merge_log', []):
                log_file = log_entry.get('file', '')
                mf = None
                for candidate in merge_files:
                    basename = os.path.basename(candidate.file.path)
                    if basename == log_file or candidate.original_filename == log_file:
                        mf = candidate
                        break
                if mf:
                    mf.is_processed = log_entry.get('status') == 'success'
                    if log_entry.get('error'):
                        mf.error_message = log_entry['error']
                    mf.save()
        else:
            project.status = 'failed'
            project.error_message = result.get('error', '병합 실패')
            project.merge_log = result
        
        project.save()
        
        logger.info(f"병합 실행 완료: {project.name} → {output_path}")
        return {'status': 'success', 'project_id': project_id, 'output': output_path}
        
    except MergeProject.DoesNotExist:
        logger.error(f"병합 프로젝트를 찾을 수 없음: {project_id}")
        raise
    except Exception as e:
        logger.error(f"병합 실행 오류: {str(e)}")
        try:
            project.status = 'failed'
            project.error_message = str(e)
            project.save()
        except Exception:
            pass
        raise self.retry(exc=e, countdown=30)
