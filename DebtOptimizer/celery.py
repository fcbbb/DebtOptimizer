import os
from celery import Celery

# 设置Django的默认设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DebtOptimizer.settings')

# 创建Celery实例
app = Celery('DebtOptimizer')

# 从Django的设置文件中加载配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动从所有已注册的Django应用中加载任务
app.autodiscover_tasks()
# 配置定时任务
from celery.schedules import crontab

app.conf.beat_schedule = {
    'periodic-ai-analysis': {
        'task': 'ai_agent.tasks.periodic_ai_analysis',
        'schedule': crontab(minute=0, hour=2),  # 每天凌晨2点执行
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
