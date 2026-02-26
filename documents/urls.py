from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentViewSet, ExtractedDataViewSet, ReportViewSet,
    MergeProjectViewSet, ColumnMappingTemplateViewSet,
)

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'extracted-data', ExtractedDataViewSet, basename='extracted-data')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'merge-projects', MergeProjectViewSet, basename='merge-project')
router.register(r'mapping-templates', ColumnMappingTemplateViewSet, basename='mapping-template')

urlpatterns = [
    path('', include(router.urls)),
]
