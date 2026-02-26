from rest_framework import serializers
from .models import (
    Document, ExtractedData, Report,
    MergeProject, MergeFile, ColumnMappingTemplate,
    Vendor, TaxEvent,
)


class DocumentSerializer(serializers.ModelSerializer):
    """문서 시리얼라이저"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = ('id', 'user', 'user_username', 'file', 'file_url', 
                  'file_type', 'file_size', 'original_filename', 
                  'status', 'created_at', 'updated_at', 'processed_at',
                  'error_message')
        read_only_fields = ('id', 'user', 'file_size', 'status', 
                           'created_at', 'updated_at', 'processed_at', 
                           'error_message')
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None
    
    def validate_file(self, value):
        # 파일 크기 검증 (10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("파일 크기는 10MB를 초과할 수 없습니다.")
        
        # 파일 유형 검증
        allowed_types = ['application/pdf', 'application/vnd.ms-excel',
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        'image/jpeg', 'image/png', 'image/jpg']
        
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("지원하지 않는 파일 형식입니다.")
        
        return value


class DocumentUploadSerializer(serializers.ModelSerializer):
    """문서 업로드 시리얼라이저"""
    class Meta:
        model = Document
        fields = ('file', 'file_type')
    
    def create(self, validated_data):
        request = self.context.get('request')
        file_obj = validated_data['file']
        
        document = Document.objects.create(
            user=request.user,
            file=file_obj,
            file_type=validated_data['file_type'],
            file_size=file_obj.size,
            original_filename=file_obj.name
        )
        
        return document


class ExtractedDataSerializer(serializers.ModelSerializer):
    """추출 데이터 시리얼라이저"""
    document_filename = serializers.CharField(
        source='document.original_filename', read_only=True
    )
    
    class Meta:
        model = ExtractedData
        fields = ('id', 'document', 'document_filename', 'extracted_text',
                  'metadata', 'structured_data', 'total_pages', 'total_rows',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class ReportSerializer(serializers.ModelSerializer):
    """리포트 시리얼라이저"""
    document_filename = serializers.CharField(
        source='document.original_filename', read_only=True
    )
    generated_by_username = serializers.CharField(
        source='generated_by.username', read_only=True
    )
    
    class Meta:
        model = Report
        fields = ('id', 'document', 'document_filename', 'title', 'summary',
                  'content', 'generated_by', 'generated_by_username',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'generated_by', 'created_at', 'updated_at')


# ========================
# 병합 프로젝트 시리얼라이저
# ========================

class MergeFileSerializer(serializers.ModelSerializer):
    """병합 파일 시리얼라이저"""
    class Meta:
        model = MergeFile
        fields = (
            'id', 'project', 'document', 'file', 'original_filename',
            'file_size', 'detected_headers', 'header_row_index',
            'total_rows', 'column_types', 'sample_data',
            'is_analyzed', 'is_processed', 'error_message', 'created_at',
        )
        read_only_fields = (
            'id', 'original_filename', 'file_size', 'detected_headers',
            'header_row_index', 'total_rows', 'column_types', 'sample_data',
            'is_analyzed', 'is_processed', 'error_message', 'created_at',
        )


class MergeFileUploadSerializer(serializers.Serializer):
    """병합 파일 업로드 시리얼라이저"""
    files = serializers.ListField(
        child=serializers.FileField(),
        min_length=1,
        max_length=50,
        help_text='엑셀 파일 목록 (최대 50개)',
    )
    
    def validate_files(self, value):
        allowed_ext = ['.xlsx', '.xls']
        for f in value:
            ext = '.' + f.name.rsplit('.', 1)[-1].lower() if '.' in f.name else ''
            if ext not in allowed_ext:
                raise serializers.ValidationError(
                    f"'{f.name}': 엑셀 파일만 업로드 가능합니다. (.xlsx, .xls)"
                )
            if f.size > 50 * 1024 * 1024:  # 50MB
                raise serializers.ValidationError(
                    f"'{f.name}': 파일 크기가 50MB를 초과합니다."
                )
        return value


class MergeProjectSerializer(serializers.ModelSerializer):
    """병합 프로젝트 시리얼라이저"""
    files = MergeFileSerializer(many=True, read_only=True)
    file_count = serializers.SerializerMethodField()
    user_username = serializers.CharField(source='user.username', read_only=True)
    merged_file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MergeProject
        fields = (
            'id', 'user', 'user_username', 'name', 'description',
            'status', 'column_mapping', 'date_columns', 'number_columns',
            'date_output_format', 'analysis_result',
            'merged_file', 'merged_file_url', 'merge_log',
            'created_at', 'updated_at', 'completed_at',
            'error_message', 'files', 'file_count',
        )
        read_only_fields = (
            'id', 'user', 'status', 'analysis_result', 'merged_file',
            'merge_log', 'created_at', 'updated_at', 'completed_at',
            'error_message',
        )
    
    def get_file_count(self, obj):
        return obj.files.count()
    
    def get_merged_file_url(self, obj):
        if obj.merged_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.merged_file.url)
        return None


class MergeProjectCreateSerializer(serializers.ModelSerializer):
    """병합 프로젝트 생성 시리얼라이저"""
    class Meta:
        model = MergeProject
        fields = ('name', 'description')
    
    def create(self, validated_data):
        request = self.context.get('request')
        return MergeProject.objects.create(
            user=request.user,
            **validated_data
        )


class MergeProjectUpdateMappingSerializer(serializers.Serializer):
    """매핑 규칙 업데이트 시리얼라이저"""
    column_mapping = serializers.DictField(
        child=serializers.CharField(),
        required=False,
        help_text='열 매핑 규칙 {"원본명": "표준명"}'
    )
    date_columns = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text='날짜 정규화 대상 열 이름'
    )
    number_columns = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text='숫자 정규화 대상 열 이름'
    )
    date_output_format = serializers.CharField(
        required=False,
        default='%Y-%m-%d',
        help_text='날짜 출력 포맷 (strftime)'
    )


class ColumnMappingTemplateSerializer(serializers.ModelSerializer):
    """매핑 템플릿 시리얼라이저"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ColumnMappingTemplate
        fields = (
            'id', 'user', 'user_username', 'name', 'description',
            'column_mapping', 'date_columns', 'number_columns',
            'date_output_format', 'custom_aliases', 'is_public',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        request = self.context.get('request')
        return ColumnMappingTemplate.objects.create(
            user=request.user,
            **validated_data
        )


class VendorSerializer(serializers.ModelSerializer):
    """거래처 시리얼라이저"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    vendor_type_display = serializers.CharField(source='get_vendor_type_display', read_only=True)
    
    class Meta:
        model = Vendor
        fields = (
            'id', 'user', 'user_username', 'name', 'business_number',
            'vendor_type', 'vendor_type_display', 'category',
            'total_income', 'total_expense', 'transaction_count',
            'contact_name', 'phone', 'email', 'address', 'memo',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'user', 'total_income', 'total_expense',
                           'transaction_count', 'created_at', 'updated_at')


class TaxEventSerializer(serializers.ModelSerializer):
    """세금 일정 시리얼라이저"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = TaxEvent
        fields = (
            'id', 'user', 'user_username', 'title', 'description',
            'due_date', 'is_completed', 'completed_at', 'amount', 'memo',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
