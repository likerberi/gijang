from django.contrib import admin
from .models import AutomationTask, AutomationStep, AutomationRun


class AutomationStepInline(admin.TabularInline):
    model = AutomationStep
    extra = 1
    ordering = ('order',)


@admin.register(AutomationTask)
class AutomationTaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'target_url', 'period_type', 'status', 'last_run_at')
    list_filter = ('status', 'period_type')
    search_fields = ('name', 'target_url')
    inlines = [AutomationStepInline]


@admin.register(AutomationRun)
class AutomationRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'status', 'started_at', 'duration_ms')
    list_filter = ('status',)
    readonly_fields = ('log',)
