from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentViewSet, ExtractedDataViewSet, ReportViewSet,
    MergeProjectViewSet, ColumnMappingTemplateViewSet,
    VendorViewSet, tax_calendar_api,
)

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'extracted-data', ExtractedDataViewSet, basename='extracted-data')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'merge-projects', MergeProjectViewSet, basename='merge-project')
router.register(r'mapping-templates', ColumnMappingTemplateViewSet, basename='mapping-template')
router.register(r'vendors', VendorViewSet, basename='vendor')

urlpatterns = [
    path('', include(router.urls)),
    path('tax-calendar/', tax_calendar_api, name='tax-calendar'),
]
