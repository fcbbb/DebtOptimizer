from rest_framework import serializers
from .models import AgentTask

class AgentTaskSerializer(serializers.ModelSerializer):
    """AI代理任务序列化器"""
    
    class Meta:
        model = AgentTask
        fields = ['id', 'task_type', 'input_data', 'status', 'result', 'error_message', 'progress', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'result', 'error_message', 'progress', 'created_at', 'updated_at']

class AgentTaskCreateSerializer(serializers.ModelSerializer):
    """AI代理任务创建序列化器"""
    
    class Meta:
        model = AgentTask
        fields = ['task_type', 'input_data']
        
    def create(self, validated_data):
        # 自动设置当前用户
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)