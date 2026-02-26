from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.urls import reverse


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """API 루트 - 사용 가능한 엔드포인트 목록"""
    return Response({
        'message': '문서 처리 자동화 API에 오신 것을 환영합니다',
        'version': '1.0.0',
        'endpoints': {
            'api_docs': request.build_absolute_uri('/api/docs/'),
            'api_schema': request.build_absolute_uri('/api/schema/'),
            'admin': request.build_absolute_uri('/admin/'),
            'users': {
                'register': request.build_absolute_uri('/api/users/register/'),
                'login': request.build_absolute_uri('/api/users/login/'),
                'token_refresh': request.build_absolute_uri('/api/users/token/refresh/'),
                'profile': request.build_absolute_uri('/api/users/profile/'),
                'me': request.build_absolute_uri('/api/users/me/'),
            },
            'documents': {
                'list': request.build_absolute_uri('/api/documents/documents/'),
                'extracted_data': request.build_absolute_uri('/api/documents/extracted-data/'),
                'reports': request.build_absolute_uri('/api/documents/reports/'),
            }
        },
        'documentation': {
            'swagger_ui': request.build_absolute_uri('/api/docs/'),
            'readme': 'README.md 파일을 참조하세요',
        }
    })
