from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AutomationTask(models.Model):
    """웹 자동화 작업 정의 — 반복 다운로드를 스켈레톤으로 정의"""

    PERIOD_CHOICES = [
        ('1d', '1일'),
        ('7d', '1주일'),
        ('1m', '1개월'),
        ('1y', '1년'),
        ('custom', '사용자 지정'),
    ]
    STATUS_CHOICES = [
        ('draft', '초안'),
        ('ready', '실행 가능'),
        ('running', '실행 중'),
        ('success', '성공'),
        ('failed', '실패'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='automation_tasks', verbose_name='사용자')
    name = models.CharField('작업 이름', max_length=200)
    description = models.TextField('설명', blank=True)

    # 대상 웹 사이트
    target_url = models.URLField('대상 URL', max_length=500)
    login_required = models.BooleanField('로그인 필요', default=False)
    login_url = models.URLField('로그인 URL', max_length=500, blank=True)
    login_credentials_key = models.CharField(
        '자격증명 키', max_length=100, blank=True,
        help_text='환경변수 또는 시크릿 매니저 키 이름'
    )

    # 기간 설정
    period_type = models.CharField('기간 유형', max_length=10, choices=PERIOD_CHOICES, default='1m')
    date_from = models.DateField('시작일', null=True, blank=True)
    date_to = models.DateField('종료일', null=True, blank=True)

    # 실행 스텝 (JSON) — 간편 모드에서 사용
    steps = models.JSONField('실행 스텝', default=list, blank=True,
                             help_text='[{"action":"click","selector":"#btn"}, ...]')

    # 다운로드 설정
    download_format = models.CharField('다운로드 형식', max_length=20, default='xlsx',
                                       choices=[('xlsx', 'Excel'), ('csv', 'CSV'), ('pdf', 'PDF')])
    download_selector = models.CharField('다운로드 버튼 셀렉터', max_length=300, blank=True,
                                          help_text='CSS selector for download button')

    # 상태
    status = models.CharField('상태', max_length=20, choices=STATUS_CHOICES, default='draft')
    last_run_at = models.DateTimeField('마지막 실행', null=True, blank=True)
    error_message = models.TextField('오류 메시지', blank=True)

    # 메타
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        verbose_name = '자동화 작업'
        verbose_name_plural = '자동화 작업 목록'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class AutomationStep(models.Model):
    """실행 스텝 — 드래그&드롭 편집용"""

    ACTION_CHOICES = [
        ('goto', '페이지 이동'),
        ('click', '클릭'),
        ('fill', '입력'),
        ('select_date', '날짜 선택 (캘린더)'),
        ('set_period', '기간 버튼 설정'),
        ('wait', '대기'),
        ('download', '다운로드 클릭'),
        ('screenshot', '스크린샷'),
        ('scroll', '스크롤'),
        ('select_option', '드롭다운 선택'),
    ]

    task = models.ForeignKey(AutomationTask, on_delete=models.CASCADE,
                             related_name='step_list', verbose_name='작업')
    order = models.IntegerField('순서', default=0)
    action = models.CharField('액션', max_length=20, choices=ACTION_CHOICES)
    selector = models.CharField('CSS 셀렉터', max_length=500, blank=True)
    value = models.CharField('값', max_length=500, blank=True,
                             help_text='입력값, URL, 날짜 등')
    description = models.CharField('설명', max_length=200, blank=True)
    wait_after = models.IntegerField('후속 대기(ms)', default=500)

    class Meta:
        verbose_name = '자동화 스텝'
        verbose_name_plural = '자동화 스텝 목록'
        ordering = ['task', 'order']

    def __str__(self):
        return f"[{self.order}] {self.get_action_display()}: {self.selector or self.value}"


class AutomationRun(models.Model):
    """실행 기록"""

    STATUS_CHOICES = [
        ('running', '실행 중'),
        ('success', '성공'),
        ('failed', '실패'),
        ('cancelled', '취소'),
    ]

    task = models.ForeignKey(AutomationTask, on_delete=models.CASCADE,
                             related_name='runs', verbose_name='작업')
    status = models.CharField('상태', max_length=20, choices=STATUS_CHOICES, default='running')
    started_at = models.DateTimeField('시작', auto_now_add=True)
    finished_at = models.DateTimeField('종료', null=True, blank=True)
    duration_ms = models.IntegerField('소요시간(ms)', null=True, blank=True)
    log = models.JSONField('실행 로그', default=list, blank=True)
    error_message = models.TextField('오류', blank=True)

    # 다운로드 결과
    downloaded_file = models.FileField('다운로드 파일', upload_to='automation/%Y/%m/%d/',
                                       null=True, blank=True)
    screenshot = models.ImageField('스크린샷', upload_to='automation/screenshots/%Y/%m/%d/',
                                    null=True, blank=True)

    class Meta:
        verbose_name = '실행 기록'
        verbose_name_plural = '실행 기록 목록'
        ordering = ['-started_at']

    def __str__(self):
        return f"Run #{self.id} - {self.task.name} ({self.get_status_display()})"

