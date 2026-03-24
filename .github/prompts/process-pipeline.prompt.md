---
description: "새 파일 유형 처리 파이프라인 추가. 기존 process_excel/process_csv 패턴으로 새 파일 포맷(JSON, XML 등) 처리 함수를 생성."
agent: "agent"
---

documents/tasks.py의 기존 처리 파이프라인 패턴을 따라 새 파일 유형의 처리 함수를 추가해줘.

## 변경 대상 파일

1. **documents/tasks.py** — `process_{type}(document)` 함수 추가
2. **documents/tasks.py** — `process_document()` 라우터에 새 유형 분기 추가
3. **documents/models.py** — `FILE_TYPE_CHOICES`에 새 유형 추가
4. **config/settings.py** — `ALLOWED_FILE_TYPES`에 MIME 타입 추가
5. **documents/serializers.py** — `validate_file()`에 MIME 타입 추가
6. **documents/models.py** — `FileExtensionValidator`에 확장자 추가

## 처리 함수 패턴 (process_excel 기준)

```python
def process_{type}(document):
    """파일 처리"""
    file_path = document.file.path

    # 1. 파일 읽기
    # 2. 헤더/데이터 분리 (가능하면 HeaderDetector 활용)
    # 3. 열 매핑 (ColumnMapper 활용)
    # 4. 정규화 (DateNormalizer, NumberNormalizer)
    # 5. 재무 열 감지 + 잔액 검증
    # 6. 계정과목 자동 분류

    # ExtractedData 저장
    ExtractedData.objects.update_or_create(
        document=document,
        defaults={
            'extracted_text': extracted_text,
            'structured_data': {
                'headers': headers,
                'rows': rows,
                'sheet_name': sheet_name,
            },
            'metadata': {
                'preprocessing': {...},
                'financial_columns': {...},
                'classification_summary': {...},
            },
            'total_rows': len(rows),
        }
    )

    # 리포트 자동 생성
    generate_report.delay(document.id)
```

## process_document 라우터 패턴

```python
@shared_task(bind=True, max_retries=3)
def process_document(self, document_id):
    document = Document.objects.get(id=document_id)
    document.status = 'processing'
    document.save()
    try:
        if document.file_type == 'excel':
            process_excel(document)
        elif document.file_type == 'csv':
            process_csv(document)
        # ← 여기에 새 유형 추가
        document.status = 'completed'
        document.processed_at = timezone.now()
        document.save()
        _send_document_notification(document, success=True)
    except Exception as e:
        document.status = 'failed'
        document.error_message = str(e)
        document.save()
        _send_document_notification(document, success=False)
        raise
```

## 규칙
- 가능하면 기존 유틸리티(HeaderDetector, ColumnMapper, normalizers) 재사용
- `ExtractedData.structured_data` 형식은 `{'headers': [...], 'rows': [...]}` 통일
- metadata에 preprocessing 정보 포함
- 이메일 알림은 process_document 래퍼에서 처리 (개별 함수에서 하지 않음)
