from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AutomationTaskViewSet

router = DefaultRouter()
router.register('tasks', AutomationTaskViewSet, basename='automation-task')

urlpatterns = [
    path('', include(router.urls)),
]
