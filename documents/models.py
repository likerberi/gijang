from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

User = get_user_model()


class Document(models.Model):
    """업로드된 문서 모델"""
    FILE_TYPE_CHOICES = [
        ('excel', '엑셀'),
        ('image', '이미지'),
        ('pdf', 'PDF'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('processing', '처리중'),
        ('completed', '완료'),
        ('failed', '실패'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, 
                            related_name='documents', verbose_name='업로드 사용자')
    file = models.FileField('파일', upload_to='documents/%Y/%m/%d/',
                           validators=[FileExtensionValidator(
                               allowed_extensions=['xlsx', 'xls', 'pdf', 'jpg', 'jpeg', 'png']
                           )])
    file_type = models.CharField('파일 유형', max_length=10, choices=FILE_TYPE_CHOICES)
    file_size = models.IntegerField('파일 크기(bytes)', default=0)
    original_filename = models.CharField('원본 파일명', max_length=255)
    
    status = models.CharField('처리 상태', max_length=20, 
                             choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    processed_at = models.DateTimeField('처리 완료일', null=True, blank=True)
    
    error_message = models.TextField('오류 메시지', blank=True)
    
    class Meta:
        verbose_name = '문서'
        verbose_name_plural = '문서 목록'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.original_filename} ({self.get_status_display()})"


class ExtractedData(models.Model):
    """추출된 데이터 모델"""
    document = models.OneToOneField(Document, on_delete=models.CASCADE,
                                   related_name='extracted_data', 
                                   verbose_name='문서')
    
    # 공통 필드
    extracted_text = models.TextField('추출된 텍스트', blank=True)
    metadata = models.JSONField('메타데이터', default=dict)
    
    # 구조화된 데이터
    structured_data = models.JSONField('구조화된 데이터', default=dict)
    
    # 통계 정보
    total_pages = models.IntegerField('총 페이지 수', default=0)
    total_rows = models.IntegerField('총 행 수', default=0)
    
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '추출 데이터'
        verbose_name_plural = '추출 데이터 목록'
    
    def __str__(self):
        return f"추출 데이터: {self.document.original_filename}"


class Report(models.Model):
    """생성된 리포트 모델"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE,
                                related_name='reports', verbose_name='문서')
    
    title = models.CharField('리포트 제목', max_length=255)
    summary = models.TextField('요약')
    content = models.JSONField('리포트 내용', default=dict)
    
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                    null=True, verbose_name='생성자')
    
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '리포트'
        verbose_name_plural = '리포트 목록'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class MergeProject(models.Model):
    """파일 병합 프로젝트 모델
    
    구조가 비슷한 여러 엑셀 파일을 통일된 규칙으로 병합하기 위한 프로젝트
    워크플로우: 샘플 분석 → 매핑 규칙 확정 → 일괄 병합 실행
    """
    STATUS_CHOICES = [
        ('draft', '초안'),
        ('analyzing', '분석중'),
        ('ready', '규칙 확정'),
        ('merging', '병합중'),
        ('completed', '완료'),
        ('failed', '실패'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                            related_name='merge_projects', verbose_name='사용자')
    name = models.CharField('프로젝트명', max_length=255)
    description = models.TextField('설명', blank=True)
    
    status = models.CharField('상태', max_length=20, 
                             choices=STATUS_CHOICES, default='draft')
    
    # 매핑 규칙 (JSON)
    column_mapping = models.JSONField('열 매핑 규칙', default=dict,
        help_text='{"원본 열이름": "표준 열이름"} 형식')
    date_columns = models.JSONField('날짜 열 목록', default=list,
        help_text='날짜 정규화 대상 열 이름 목록')
    number_columns = models.JSONField('숫자 열 목록', default=list,
        help_text='숫자 정규화 대상 열 이름 목록')
    
    # 분석 결과 (JSON)
    analysis_result = models.JSONField('분석 결과', default=dict, blank=True)
    
    # 날짜 출력 포맷
    date_output_format = models.CharField('날짜 출력 포맷', max_length=50, 
                                         default='%Y-%m-%d')
    
    # 병합 결과
    merged_file = models.FileField('병합 결과 파일', 
                                   upload_to='merged/%Y/%m/%d/', 
                                   null=True, blank=True)
    merge_log = models.JSONField('병합 로그', default=dict, blank=True)
    
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    completed_at = models.DateTimeField('완료일', null=True, blank=True)
    
    error_message = models.TextField('오류 메시지', blank=True)
    
    class Meta:
        verbose_name = '병합 프로젝트'
        verbose_name_plural = '병합 프로젝트 목록'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class MergeFile(models.Model):
    """병합 프로젝트에 포함된 파일"""
    project = models.ForeignKey(MergeProject, on_delete=models.CASCADE,
                               related_name='files', verbose_name='병합 프로젝트')
    document = models.ForeignKey(Document, on_delete=models.CASCADE,
                                related_name='merge_files', verbose_name='문서',
                                null=True, blank=True)
    file = models.FileField('파일', upload_to='merge_sources/%Y/%m/%d/',
                           validators=[FileExtensionValidator(
                               allowed_extensions=['xlsx', 'xls']
                           )])
    original_filename = models.CharField('원본 파일명', max_length=255)
    file_size = models.IntegerField('파일 크기(bytes)', default=0)
    
    # 개별 파일 분석 결과
    detected_headers = models.JSONField('탐지된 헤더', default=list)
    header_row_index = models.IntegerField('헤더 행 인덱스', default=0)
    total_rows = models.IntegerField('총 행 수', default=0)
    column_types = models.JSONField('열 타입', default=dict)
    sample_data = models.JSONField('샘플 데이터', default=list)
    
    # 처리 상태
    is_analyzed = models.BooleanField('분석 완료', default=False)
    is_processed = models.BooleanField('처리 완료', default=False)
    error_message = models.TextField('오류 메시지', blank=True)
    
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    
    class Meta:
        verbose_name = '병합 파일'
        verbose_name_plural = '병합 파일 목록'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.original_filename} → {self.project.name}"


class ColumnMappingTemplate(models.Model):
    """재사용 가능한 열 매핑 템플릿
    
    자주 사용하는 매핑 규칙을 저장해서 반복 업무에 활용
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                            related_name='mapping_templates', verbose_name='사용자')
    name = models.CharField('템플릿명', max_length=255)
    description = models.TextField('설명', blank=True)
    
    # 매핑 규칙
    column_mapping = models.JSONField('열 매핑 규칙', default=dict)
    date_columns = models.JSONField('날짜 열 목록', default=list)
    number_columns = models.JSONField('숫자 열 목록', default=list)
    date_output_format = models.CharField('날짜 출력 포맷', max_length=50, 
                                         default='%Y-%m-%d')
    
    # 커스텀 별칭 (기본 매핑 외 추가)
    custom_aliases = models.JSONField('커스텀 별칭', default=dict,
        help_text='{"표준명": ["별칭1", "별칭2"]} 형식')
    
    is_public = models.BooleanField('공개 여부', default=False,
        help_text='다른 사용자도 사용 가능 여부')
    
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '매핑 템플릿'
        verbose_name_plural = '매핑 템플릿 목록'
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.name


class Vendor(models.Model):
    """거래처 모델
    
    거래 내역에서 자동 추출되거나 수동 등록된 거래처 정보
    """
    VENDOR_TYPE_CHOICES = [
        ('customer', '매출처 (고객)'),
        ('supplier', '매입처 (거래처)'),
        ('both', '매출/매입 겸용'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                            related_name='vendors', verbose_name='사용자')
    name = models.CharField('거래처명', max_length=255)
    business_number = models.CharField('사업자번호', max_length=20, blank=True,
        help_text='000-00-00000 형식')
    vendor_type = models.CharField('거래처 유형', max_length=10, 
                                  choices=VENDOR_TYPE_CHOICES, default='supplier')
    category = models.CharField('계정과목', max_length=50, blank=True,
        help_text='주 거래 계정과목')
    
    # 거래 통계 (자동 갱신)
    total_income = models.FloatField('총 입금액', default=0)
    total_expense = models.FloatField('총 출금액', default=0)
    transaction_count = models.IntegerField('거래 건수', default=0)
    
    # 연락처
    contact_name = models.CharField('담당자명', max_length=100, blank=True)
    phone = models.CharField('전화번호', max_length=20, blank=True)
    email = models.EmailField('이메일', blank=True)
    address = models.TextField('주소', blank=True)
    
    memo = models.TextField('메모', blank=True)
    
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '거래처'
        verbose_name_plural = '거래처 목록'
        ordering = ['-transaction_count']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_vendor_type_display()})"


class TaxEvent(models.Model):
    """세금 일정 (사용자 커스텀)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                            related_name='tax_events', verbose_name='사용자')
    title = models.CharField('일정명', max_length=255)
    description = models.TextField('설명', blank=True)
    due_date = models.DateField('마감일')
    is_completed = models.BooleanField('완료 여부', default=False)
    completed_at = models.DateTimeField('완료일', null=True, blank=True)
    amount = models.FloatField('납부 금액', default=0, blank=True)
    memo = models.TextField('메모', blank=True)
    
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '세금 일정'
        verbose_name_plural = '세금 일정 목록'
        ordering = ['due_date']
    
    def __str__(self):
        return f"{self.title} ({self.due_date})"


class ClassificationRule(models.Model):
    """분류 학습 규칙 — 사용자 수정 이력을 축적하여 자동분류 정확도 향상
    
    키워드/거래처명 → 계정과목 매핑을 저장하고,
    새 파일 업로드 시 키워드 매칭보다 우선 적용.
    """
    MATCH_TYPE_CHOICES = [
        ('exact', '정확히 일치'),
        ('contains', '포함'),
        ('vendor', '거래처명'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                            related_name='classification_rules', verbose_name='사용자')
    pattern = models.CharField('패턴', max_length=255,
        help_text='매칭할 문자열 (적요 또는 거래처명)')
    match_type = models.CharField('매칭 방식', max_length=10,
                                 choices=MATCH_TYPE_CHOICES, default='contains')
    category = models.CharField('계정과목', max_length=50)
    
    # 학습 추적
    source = models.CharField('생성 출처', max_length=20, default='user',
        help_text='user=수동수정, auto=자동학습, vendor=거래처기반')
    hit_count = models.IntegerField('적용 횟수', default=0)
    
    priority = models.IntegerField('우선순위', default=10,
        help_text='낮은 숫자가 높은 우선순위 (user=10, vendor=20, auto=30)')
    
    is_active = models.BooleanField('활성', default=True)
    
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '분류 규칙'
        verbose_name_plural = '분류 규칙 목록'
        ordering = ['priority', '-hit_count']
        unique_together = ['user', 'pattern', 'match_type']
    
    def __str__(self):
        return f"{self.pattern} → {self.category} ({self.get_match_type_display()})"

