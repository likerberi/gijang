from celery import Celery
from ..core.config import settings

celery_app = Celery(
    "fastapi_document_processor",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
)

# 태스크 import (Celery가 태스크를 찾도록)
from . import document_tasks  # noqa
