from django.contrib import admin
from .models import Document, ExtractedData, Report, MergeProject, MergeFile, ColumnMappingTemplate, Vendor, TaxEvent


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'file_type', 'status', 'user', 
                   'file_size', 'created_at', 'processed_at')
    list_filter = ('file_type', 'status', 'created_at')
    search_fields = ('original_filename', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'processed_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('파일 정보', {
            'fields': ('user', 'file', 'original_filename', 'file_type', 'file_size')
        }),
        ('처리 상태', {
            'fields': ('status', 'error_message', 'processed_at')
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExtractedData)
class ExtractedDataAdmin(admin.ModelAdmin):
    list_display = ('document', 'total_pages', 'total_rows', 'created_at')
    search_fields = ('document__original_filename',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


class MergeFileInline(admin.TabularInline):
    model = MergeFile
    extra = 0
    readonly_fields = ('original_filename', 'file_size', 'detected_headers', 
                       'header_row_index', 'total_rows', 'is_analyzed', 'is_processed')
    fields = ('file', 'original_filename', 'file_size', 'is_analyzed', 'is_processed', 'error_message')


@admin.register(MergeProject)
class MergeProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'status', 'file_count', 'created_at', 'completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'analysis_result', 'merge_log')
    ordering = ('-created_at',)
    inlines = [MergeFileInline]
    
    def file_count(self, obj):
        return obj.files.count()
    file_count.short_description = '파일 수'


@admin.register(ColumnMappingTemplate)
class ColumnMappingTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_public', 'created_at', 'updated_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('name', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-updated_at',)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'document', 'generated_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'summary', 'document__original_filename')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor_type', 'category', 'transaction_count',
                   'total_income', 'total_expense', 'user', 'created_at')
    list_filter = ('vendor_type', 'category', 'created_at')
    search_fields = ('name', 'business_number', 'memo', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-transaction_count',)


@admin.register(TaxEvent)
class TaxEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'due_date', 'is_completed', 'amount', 'user', 'created_at')
    list_filter = ('is_completed', 'due_date')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('due_date',)

