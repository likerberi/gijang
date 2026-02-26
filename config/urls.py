"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import api_root
from .frontend_views import (
    login_view, dashboard_view, documents_view, document_detail_view,
    merge_view, mapping_templates_view, guide_view,
    vat_report_view, monthly_report_view, vendors_view, tax_calendar_view,
)

urlpatterns = [
    # 프론트엔드 페이지
    path('accounts/login/', login_view, name='login'),
    path('app/', dashboard_view, name='dashboard'),
    path('app/documents/', documents_view, name='documents'),
    path('app/documents/<int:doc_id>/', document_detail_view, name='document-detail'),
    path('app/documents/<int:doc_id>/vat/', vat_report_view, name='vat-report'),
    path('app/documents/<int:doc_id>/monthly/', monthly_report_view, name='monthly-report'),
    path('app/merge/', merge_view, name='merge'),
    path('app/templates/', mapping_templates_view, name='mapping-templates'),
    path('app/vendors/', vendors_view, name='vendors'),
    path('app/tax-calendar/', tax_calendar_view, name='tax-calendar'),
    path('guide/', guide_view, name='guide'),

    # API
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/documents/', include('documents.urls')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
