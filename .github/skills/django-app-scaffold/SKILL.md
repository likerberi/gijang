---
name: django-app-scaffold
description: "새 Django 앱 스캐폴딩. USE FOR: 새 앱 추가, 모델/뷰/시리얼라이저/URL/어드민/템플릿 일괄 생성, Celery 태스크 추가. 기장 프로젝트 컨벤션(ViewSet, _dispatch_task, JWT, 사이드바)을 자동 적용."
---

# Django App Scaffold

기장 프로젝트에 새 Django 앱을 추가할 때 사용합니다.
기존 앱(documents, automation, users)의 컨벤션을 그대로 따릅니다.

## When to Use
- 새 앱(기능 모듈)을 추가할 때
- 기존 앱에 새 모델 + ViewSet 세트를 추가할 때

## 프로젝트 컨벤션

### 모델 패턴
```python
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class MyModel(models.Model):
    """한줄 설명"""
    STATUS_CHOICES = [
        ('pending', '대기'),
        ('completed', '완료'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='my_models', verbose_name='사용자')
    name = models.CharField('이름', max_length=200)
    status = models.CharField('상태', max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        verbose_name = '내 모델'
        verbose_name_plural = '내 모델 목록'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
```

**규칙:**
- `User = get_user_model()` 사용 (settings.AUTH_USER_MODEL 아님)
- ForeignKey에 `related_name`, `verbose_name` 필수
- 모든 필드에 한국어 `verbose_name` 첫 인자
- `created_at` / `updated_at` 항상 포함
- `Meta`에 `verbose_name`, `verbose_name_plural`, `ordering` 필수
- `__str__` 필수

### ViewSet 패턴
```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class MyModelViewSet(viewsets.ModelViewSet):
    """내 모델 뷰셋"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MyModel.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return MyModelCreateSerializer
        if self.action == 'list':
            return MyModelListSerializer
        return MyModelDetailSerializer

    @action(detail=True, methods=['post'])
    def custom_action(self, request, pk=None):
        obj = self.get_object()
        # ...
        return Response({'message': '완료'})
```

**규칙:**
- `permission_classes = [IsAuthenticated]` 항상
- `get_queryset`에서 `user=self.request.user` 필터링 (소유권 격리)
- `get_serializer_class`로 create/list/detail 시리얼라이저 분리
- Celery 태스크는 `_dispatch_task()` 로 디스패치 (worker 미감지 시 동기 폴백)

### Serializer 패턴
```python
class MyModelSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = MyModel
        fields = ('id', 'user', 'user_username', ...)
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

class MyModelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = ('name', 'description')

    def create(self, validated_data):
        request = self.context.get('request')
        return MyModel.objects.create(user=request.user, **validated_data)
```

### URL 패턴
```python
# <app>/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MyModelViewSet

router = DefaultRouter()
router.register('items', MyModelViewSet, basename='my-item')

urlpatterns = [
    path('', include(router.urls)),
]
```

### config/urls.py 등록
```python
# API 라우트 추가
path('api/myapp/', include('myapp.urls')),

# 프론트엔드 페이지 추가
path('app/mypage/', mypage_view, name='mypage'),
```

### 프론트엔드 뷰 (config/frontend_views.py)
```python
def mypage_view(request):
    """내 페이지"""
    return render(request, 'mypage.html')
```

### Admin 등록
```python
from django.contrib import admin
from .models import MyModel

@admin.register(MyModel)
class MyModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('name',)
```

### 사이드바 메뉴 추가 (templates/base.html)
```html
<a href="/app/mypage/" class="nav-item {% block nav_mypage %}{% endblock %}" data-page="mypage">
  <span class="nav-icon">🆕</span> 내 페이지
</a>
```

### Celery 태스크 패턴
```python
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def my_task(self, obj_id):
    try:
        obj = MyModel.objects.get(id=obj_id)
        obj.status = 'processing'
        obj.save()
        # ... 처리 ...
        obj.status = 'completed'
        obj.save()
    except Exception as e:
        obj.status = 'failed'
        obj.error_message = str(e)
        obj.save()
        raise
```

## Procedure

1. `python manage.py startapp <appname>` 실행
2. `<appname>/models.py` 작성 (위 모델 패턴)
3. `<appname>/serializers.py` 작성 (위 시리얼라이저 패턴)
4. `<appname>/views.py` 작성 (위 ViewSet 패턴 + `_dispatch_task` 임포트)
5. `<appname>/urls.py` 작성 (DefaultRouter)
6. `<appname>/admin.py` 작성
7. `config/settings.py` → `INSTALLED_APPS`에 추가
8. `config/urls.py` → API 라우트 + 프론트엔드 라우트 추가
9. `config/frontend_views.py` → 뷰 함수 추가
10. `templates/<pagename>.html` → base.html 상속 템플릿 생성
11. `templates/base.html` → 사이드바 메뉴 항목 추가
12. `python manage.py makemigrations <appname> && python manage.py migrate`
13. `copilot-instructions.md` → 새 앱 정보 반영
