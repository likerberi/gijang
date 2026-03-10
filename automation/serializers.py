from rest_framework import serializers
from .models import AutomationTask, AutomationStep, AutomationRun


class AutomationStepSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = AutomationStep
        fields = ('id', 'order', 'action', 'action_display', 'selector',
                  'value', 'description', 'wait_after')


class AutomationRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationRun
        fields = ('id', 'status', 'started_at', 'finished_at', 'duration_ms',
                  'log', 'error_message', 'downloaded_file', 'screenshot')
        read_only_fields = ('id', 'started_at', 'finished_at', 'duration_ms',
                            'log', 'error_message', 'downloaded_file', 'screenshot')


class AutomationTaskListSerializer(serializers.ModelSerializer):
    """목록용 간략 시리얼라이저"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    period_display = serializers.CharField(source='get_period_type_display', read_only=True)
    step_count = serializers.IntegerField(source='step_list.count', read_only=True)
    run_count = serializers.IntegerField(source='runs.count', read_only=True)

    class Meta:
        model = AutomationTask
        fields = ('id', 'name', 'description', 'target_url', 'period_type',
                  'period_display', 'status', 'status_display', 'step_count',
                  'run_count', 'last_run_at', 'created_at', 'updated_at')


class AutomationTaskDetailSerializer(serializers.ModelSerializer):
    """상세/생성용 시리얼라이저"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    period_display = serializers.CharField(source='get_period_type_display', read_only=True)
    step_list = AutomationStepSerializer(many=True, read_only=True)
    recent_runs = serializers.SerializerMethodField()

    class Meta:
        model = AutomationTask
        fields = ('id', 'name', 'description', 'target_url', 'login_required',
                  'login_url', 'login_credentials_key', 'period_type',
                  'period_display', 'date_from', 'date_to', 'steps',
                  'download_format', 'download_selector', 'status',
                  'status_display', 'last_run_at', 'error_message',
                  'step_list', 'recent_runs',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'status', 'last_run_at', 'error_message',
                            'created_at', 'updated_at')

    def get_recent_runs(self, obj):
        runs = obj.runs.all()[:5]
        return AutomationRunSerializer(runs, many=True).data


class AutomationTaskCreateSerializer(serializers.ModelSerializer):
    """작업 생성 시리얼라이저"""
    class Meta:
        model = AutomationTask
        fields = ('id', 'name', 'description', 'target_url', 'login_required',
                  'login_url', 'period_type', 'date_from', 'date_to',
                  'steps', 'download_format', 'download_selector')
        read_only_fields = ('id',)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
