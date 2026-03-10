from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import logging

from .models import AutomationTask, AutomationStep, AutomationRun
from .serializers import (
    AutomationTaskListSerializer,
    AutomationTaskDetailSerializer,
    AutomationTaskCreateSerializer,
    AutomationStepSerializer,
    AutomationRunSerializer,
)

logger = logging.getLogger(__name__)


class AutomationTaskViewSet(viewsets.ModelViewSet):
    """자동화 작업 CRUD + 실행"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AutomationTask.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return AutomationTaskCreateSerializer
        if self.action == 'list':
            return AutomationTaskListSerializer
        return AutomationTaskDetailSerializer

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """작업 실행"""
        task = self.get_object()

        if task.status == 'running':
            return Response(
                {'error': '이미 실행 중인 작업입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 실행 기록 생성
        run_obj = AutomationRun.objects.create(task=task, status='running')
        task.status = 'running'
        task.save()

        # 동기 실행 (Celery 없이도 동작)
        try:
            from .engine import run_automation
            run_automation(task, run_obj)
        except Exception as e:
            run_obj.status = 'failed'
            run_obj.error_message = str(e)
            run_obj.finished_at = timezone.now()
            run_obj.save()
            task.status = 'failed'
            task.error_message = str(e)
            task.save()

        # 갱신된 run 반환
        run_obj.refresh_from_db()
        serializer = AutomationRunSerializer(run_obj)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def runs(self, request, pk=None):
        """실행 기록 조회"""
        task = self.get_object()
        runs = task.runs.all()[:20]
        serializer = AutomationRunSerializer(runs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_step(self, request, pk=None):
        """스텝 추가"""
        task = self.get_object()
        serializer = AutomationStepSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        last_order = task.step_list.count()
        serializer.save(task=task, order=last_order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put'])
    def update_steps(self, request, pk=None):
        """스텝 전체 교체 (순서 포함)"""
        task = self.get_object()
        steps_data = request.data.get('steps', [])

        # 기존 삭제 후 재생성
        task.step_list.all().delete()
        created = []
        for i, step_data in enumerate(steps_data):
            step_data['order'] = i
            serializer = AutomationStepSerializer(data=step_data)
            serializer.is_valid(raise_exception=True)
            obj = serializer.save(task=task, order=i)
            created.append(obj)

        # 스텝이 있으면 ready로 전환
        if created:
            task.status = 'ready'
            task.save()

        serializer = AutomationStepSerializer(created, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def dry_run(self, request, pk=None):
        """드라이런 — 스텝을 검증만 하고 실행하지 않음"""
        task = self.get_object()
        steps = task.step_list.all().order_by('order')
        if not steps.exists():
            steps_json = task.steps or []
        else:
            steps_json = AutomationStepSerializer(steps, many=True).data

        from .engine import calculate_date_range
        date_from, date_to = calculate_date_range(
            task.period_type, task.date_from, task.date_to
        )

        report = {
            'task_name': task.name,
            'target_url': task.target_url,
            'date_range': {'from': str(date_from), 'to': str(date_to)},
            'period': task.get_period_type_display(),
            'total_steps': len(steps_json),
            'steps': steps_json,
            'download_format': task.download_format,
            'download_selector': task.download_selector,
            'validation': _validate_steps(steps_json),
        }
        return Response(report)

    @action(detail=False, methods=['get'])
    def presets(self, request):
        """사전 정의된 자동화 프리셋 (참고용 템플릿)"""
        presets = [
            {
                'name': '홈택스 — 세금계산서 목록 다운로드',
                'target_url': 'https://www.hometax.go.kr',
                'login_required': True,
                'period_type': '1m',
                'download_format': 'xlsx',
                'steps': [
                    {'action': 'goto', 'value': 'https://www.hometax.go.kr', 'description': '홈택스 이동'},
                    {'action': 'click', 'selector': '#menu-tax-invoice', 'description': '세금계산서 메뉴'},
                    {'action': 'select_date', 'selector': '#date-from', 'value': '{{date_from}}', 'description': '시작일 선택'},
                    {'action': 'select_date', 'selector': '#date-to', 'value': '{{date_to}}', 'description': '종료일 선택'},
                    {'action': 'click', 'selector': '#btn-search', 'description': '조회'},
                    {'action': 'download', 'selector': '#btn-excel-download', 'description': '엑셀 다운로드'},
                ],
            },
            {
                'name': '카드사 — 월별 이용내역 다운로드',
                'target_url': 'https://www.cardcompany.co.kr',
                'login_required': True,
                'period_type': '1m',
                'download_format': 'xlsx',
                'steps': [
                    {'action': 'goto', 'value': 'https://www.cardcompany.co.kr/statement', 'description': '이용내역 이동'},
                    {'action': 'set_period', 'selector': '#btn-1month', 'description': '1개월 선택'},
                    {'action': 'click', 'selector': '#btn-search', 'description': '조회'},
                    {'action': 'wait', 'value': '2000', 'description': '로딩 대기'},
                    {'action': 'download', 'selector': '#btn-download-excel', 'description': '엑셀 다운로드'},
                ],
            },
            {
                'name': '은행 — 거래내역 다운로드',
                'target_url': 'https://www.bank.co.kr',
                'login_required': True,
                'period_type': '1m',
                'download_format': 'xlsx',
                'steps': [
                    {'action': 'goto', 'value': 'https://www.bank.co.kr/account/history', 'description': '거래내역 이동'},
                    {'action': 'click', 'selector': '#account-select', 'description': '계좌 선택'},
                    {'action': 'select_date', 'selector': '#startDate', 'value': '{{date_from}}', 'description': '시작일'},
                    {'action': 'select_date', 'selector': '#endDate', 'value': '{{date_to}}', 'description': '종료일'},
                    {'action': 'click', 'selector': '#btn-search', 'description': '조회'},
                    {'action': 'download', 'selector': '.btn-excel', 'description': '엑셀 다운로드'},
                ],
            },
        ]
        return Response(presets)


def _validate_steps(steps):
    """스텝 유효성 검사"""
    issues = []
    has_download = False

    for i, step in enumerate(steps):
        s = step if isinstance(step, dict) else step
        action = s.get('action', '')
        selector = s.get('selector', '')
        value = s.get('value', '')

        if action in ('click', 'fill', 'select_date', 'set_period', 'download', 'select_option'):
            if not selector:
                issues.append(f'Step {i + 1}: "{action}" 액션에 CSS 셀렉터가 필요합니다.')
        if action == 'fill' and not value:
            issues.append(f'Step {i + 1}: "fill" 액션에 입력값이 필요합니다.')
        if action == 'goto' and not value:
            issues.append(f'Step {i + 1}: "goto" 액션에 URL이 필요합니다.')
        if action == 'download':
            has_download = True

    if not has_download:
        issues.append('다운로드 스텝이 없습니다. 결과 파일을 받으려면 "download" 스텝을 추가하세요.')

    return {'valid': len(issues) == 0, 'issues': issues}

