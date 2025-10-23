from django.db import models
from django.contrib.auth.models import User
import uuid

class AgentTask(models.Model):
    """AI代理任务模型"""
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    task_type = models.CharField(max_length=100, verbose_name="任务类型")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="状态")
    input_data = models.TextField(verbose_name="输入数据")
    result = models.TextField(blank=True, null=True, verbose_name="结果")
    error_message = models.TextField(blank=True, null=True, verbose_name="错误信息")
    progress = models.IntegerField(default=0, verbose_name="进度")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="完成时间")
    
    class Meta:
        verbose_name = "AI代理任务"
        verbose_name_plural = "AI代理任务"
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.task_type} - {self.status}"
        
    def to_dict(self):
        """将模型实例转换为字典"""
        return {
            'id': str(self.id),
            'task_type': self.task_type,
            'status': self.status,
            'input_data': self.input_data,
            'result': self.result,
            'error_message': self.error_message,
            'progress': self.progress,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
