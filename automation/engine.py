"""
Playwright 기반 브라우저 자동화 엔진
— 스텝 액션을 순차 실행하고 결과를 AutomationRun에 기록
"""
import logging
import time
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

# Playwright는 선택 의존성 — 없으면 graceful fallback
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    logger.warning("playwright 미설치 — pip install playwright && playwright install chromium")


def calculate_date_range(period_type, date_from=None, date_to=None):
    """기간 유형에서 실제 날짜 범위 계산"""
    today = datetime.today().date()
    if period_type == 'custom' and date_from and date_to:
        return date_from, date_to
    elif period_type == '1d':
        return today, today
    elif period_type == '7d':
        return today - timedelta(days=6), today
    elif period_type == '1m':
        return today - relativedelta(months=1) + timedelta(days=1), today
    elif period_type == '1y':
        return today - relativedelta(years=1) + timedelta(days=1), today
    return today, today


def run_automation(task, run_obj):
    """
    AutomationTask의 스텝을 Playwright로 실행.
    run_obj: AutomationRun 인스턴스 (로그 기록용)
    """
    if not HAS_PLAYWRIGHT:
        run_obj.status = 'failed'
        run_obj.error_message = 'playwright가 설치되어 있지 않습니다. pip install playwright && playwright install chromium'
        run_obj.finished_at = timezone.now()
        run_obj.save()
        task.status = 'failed'
        task.error_message = run_obj.error_message
        task.last_run_at = timezone.now()
        task.save()
        return

    log_entries = []
    start_time = time.time()

    def log(msg, level='info'):
        entry = {'time': datetime.now().isoformat(), 'level': level, 'message': msg}
        log_entries.append(entry)
        logger.info(f"[Automation #{task.id}] {msg}")

    download_dir = os.path.join('media', 'automation', datetime.now().strftime('%Y/%m/%d'))
    os.makedirs(download_dir, exist_ok=True)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            context = browser.new_context(
                accept_downloads=True,
                locale='ko-KR',
                timezone_id='Asia/Seoul',
            )
            page = context.new_page()
            log(f"브라우저 시작, 대상: {task.target_url}")

            # 날짜 범위 계산
            date_from, date_to = calculate_date_range(
                task.period_type, task.date_from, task.date_to
            )
            log(f"기간: {date_from} ~ {date_to} ({task.get_period_type_display()})")

            # 로그인 처리
            if task.login_required and task.login_url:
                log(f"로그인 페이지 이동: {task.login_url}")
                page.goto(task.login_url, wait_until='networkidle')
                # TODO: 자격증명으로 로그인 — 현재는 스텝에서 fill 액션으로 처리
                page.wait_for_timeout(1000)

            # 스텝 실행
            steps = task.step_list.all().order_by('order')
            if not steps.exists():
                # JSON steps 폴백 (간편 모드)
                steps = task.steps or []
                for i, step in enumerate(steps):
                    _execute_step_dict(page, step, i, date_from, date_to, download_dir, log)
            else:
                for step in steps:
                    _execute_step_obj(page, step, date_from, date_to, download_dir, log)

            # 최종 스크린샷
            screenshot_path = os.path.join(download_dir, f'task_{task.id}_final.png')
            page.screenshot(path=screenshot_path, full_page=True)
            log("최종 스크린샷 저장")

            # 다운로드 대기 (마지막 다운로드)
            page.wait_for_timeout(2000)

            browser.close()

        elapsed = int((time.time() - start_time) * 1000)
        run_obj.status = 'success'
        run_obj.duration_ms = elapsed
        run_obj.log = log_entries
        run_obj.finished_at = timezone.now()
        if os.path.exists(screenshot_path):
            run_obj.screenshot = screenshot_path.replace('media/', '')

        # 다운로드된 파일 찾기
        downloaded = _find_latest_download(download_dir)
        if downloaded:
            run_obj.downloaded_file = downloaded.replace('media/', '')
            log(f"다운로드 파일: {downloaded}")

        run_obj.save()

        # 태스크 상태 업데이트
        task.status = 'success'
        task.last_run_at = timezone.now()
        task.error_message = ''
        task.save()
        log(f"완료 — {elapsed}ms 소요")

    except Exception as e:
        elapsed = int((time.time() - start_time) * 1000)
        log(f"실행 오류: {str(e)}", level='error')
        run_obj.status = 'failed'
        run_obj.duration_ms = elapsed
        run_obj.error_message = str(e)
        run_obj.log = log_entries
        run_obj.finished_at = timezone.now()
        run_obj.save()

        task.status = 'failed'
        task.error_message = str(e)
        task.last_run_at = timezone.now()
        task.save()


def _execute_step_dict(page, step, index, date_from, date_to, download_dir, log):
    """JSON dict 형태 스텝 실행"""
    action = step.get('action', '')
    selector = step.get('selector', '')
    value = step.get('value', '')
    wait_after = step.get('wait_after', 500)
    desc = step.get('description', f'Step {index + 1}')

    _do_action(page, action, selector, value, wait_after, date_from, date_to, download_dir, log, desc)


def _execute_step_obj(page, step, date_from, date_to, download_dir, log):
    """AutomationStep 모델 인스턴스 실행"""
    _do_action(
        page, step.action, step.selector, step.value,
        step.wait_after, date_from, date_to, download_dir, log,
        step.description or f'Step {step.order}'
    )


def _do_action(page, action, selector, value, wait_after, date_from, date_to, download_dir, log, desc):
    """개별 액션 수행"""
    # 값에서 날짜 치환
    value = _substitute_dates(value, date_from, date_to)
    log(f"[{desc}] {action}: {selector or value}")

    try:
        if action == 'goto':
            url = value or selector
            page.goto(url, wait_until='networkidle')

        elif action == 'click':
            page.wait_for_selector(selector, timeout=10000)
            page.click(selector)

        elif action == 'fill':
            page.wait_for_selector(selector, timeout=10000)
            page.fill(selector, value)

        elif action == 'select_date':
            # 달력 UI에서 날짜 선택 — 셀렉터 클릭 후 날짜 텍스트 입력
            page.wait_for_selector(selector, timeout=10000)
            page.click(selector)
            page.wait_for_timeout(500)
            # 날짜 입력 필드를 비우고 새 날짜를 입력
            page.fill(selector, value)

        elif action == 'set_period':
            # 기간 버튼 클릭 (1일/7일/1달/1년)
            page.wait_for_selector(selector, timeout=10000)
            page.click(selector)

        elif action == 'wait':
            ms = int(value) if value else wait_after
            page.wait_for_timeout(ms)

        elif action == 'download':
            page.wait_for_selector(selector, timeout=10000)
            with page.expect_download(timeout=30000) as download_info:
                page.click(selector)
            download = download_info.value
            dest = os.path.join(download_dir, download.suggested_filename or f'download_{int(time.time())}')
            download.save_as(dest)
            log(f"다운로드 저장: {dest}")

        elif action == 'screenshot':
            path = os.path.join(download_dir, f'step_{desc}.png')
            page.screenshot(path=path)
            log(f"스크린샷 저장: {path}")

        elif action == 'scroll':
            page.evaluate(f'window.scrollBy(0, {value or 500})')

        elif action == 'select_option':
            page.wait_for_selector(selector, timeout=10000)
            page.select_option(selector, value)

        else:
            log(f"알 수 없는 액션: {action}", level='warning')

    except Exception as e:
        log(f"[{desc}] 오류: {str(e)}", level='error')
        raise

    if wait_after:
        page.wait_for_timeout(wait_after)


def _substitute_dates(value, date_from, date_to):
    """값에서 {{date_from}}, {{date_to}} 등 치환"""
    if not value:
        return value
    return (
        value
        .replace('{{date_from}}', date_from.strftime('%Y-%m-%d') if date_from else '')
        .replace('{{date_to}}', date_to.strftime('%Y-%m-%d') if date_to else '')
        .replace('{{date_from_slash}}', date_from.strftime('%Y/%m/%d') if date_from else '')
        .replace('{{date_to_slash}}', date_to.strftime('%Y/%m/%d') if date_to else '')
        .replace('{{date_from_dot}}', date_from.strftime('%Y.%m.%d') if date_from else '')
        .replace('{{date_to_dot}}', date_to.strftime('%Y.%m.%d') if date_to else '')
    )


def _find_latest_download(download_dir):
    """다운로드 디렉토리에서 가장 최근 파일 찾기"""
    if not os.path.isdir(download_dir):
        return None
    files = [
        os.path.join(download_dir, f)
        for f in os.listdir(download_dir)
        if not f.endswith('.png')  # 스크린샷 제외
    ]
    if not files:
        return None
    return max(files, key=os.path.getmtime)
