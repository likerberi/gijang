"""프론트엔드 페이지 뷰"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def login_view(request):
    """로그인 페이지"""
    return render(request, 'login.html')


def dashboard_view(request):
    """대시보드"""
    return render(request, 'dashboard.html')


def documents_view(request):
    """문서 관리"""
    return render(request, 'documents.html')


def document_detail_view(request, doc_id):
    """문서 상세 (거래내역)"""
    return render(request, 'document_detail.html', {'doc_id': doc_id})


def merge_view(request):
    """파일 병합"""
    return render(request, 'merge.html')


def mapping_templates_view(request):
    """매핑 템플릿"""
    return render(request, 'mapping_templates.html')


def guide_view(request):
    """사용 가이드"""
    return render(request, 'guide.html')
