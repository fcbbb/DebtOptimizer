from celery import shared_task
from .models import AgentTask
from .llm_use.llm_chat import get_debt_analysis, get_repayment_plan, get_financial_advice
import logging
import time
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

@shared_task
def process_agent_task(task_id):
    """
    处理AI Agent任务的Celery任务
    """
    try:
        # 获取任务实例
        task = AgentTask.objects.get(id=task_id)
        task.status = 'running'
        task.save()
        # 发送WebSocket更新
        send_task_update(task)
        
        logger.info(f"开始处理AI Agent任务 {task_id}")
        
        # 根据任务类型执行不同的处理逻辑
        if task.task_type == 'debt_analysis':
            result = get_debt_analysis(task.input_data)
        elif task.task_type == 'repayment_plan':
            # 这里需要解析input_data以获取预算信息
            result = get_repayment_plan(task.input_data, "5000")  # 默认预算5000元，实际应该从input_data解析
        elif task.task_type == 'financial_advice':
            result = get_financial_advice(task.input_data)
        else:
            result = f"未知的任务类型: {task.task_type}"
        
        # 更新任务状态为完成
        task.status = 'completed'
        task.result = result
        task.save()
        # 发送WebSocket更新
        send_task_update(task)
        
        logger.info(f"AI Agent任务 {task_id} 处理完成")
        return result
    except AgentTask.DoesNotExist:
        logger.error(f"AI Agent任务 {task_id} 不存在")
        return f"任务 {task_id} 不存在"
    except Exception as e:
        # 更新任务状态为失败
        if AgentTask.objects.filter(id=task_id).exists():
            task = AgentTask.objects.get(id=task_id)
            task.status = 'failed'
            task.error_message = str(e)
            task.save()
            # 发送WebSocket更新
            send_task_update(task)
        logger.error(f"处理AI Agent任务 {task_id} 时出错: {str(e)}")
        return f"处理任务时出错: {str(e)}"

def send_task_update(task):
    """
    发送任务更新到WebSocket
    """
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'agent_task_{task.id}',
            {
                'type': 'send_task_update',
                'status': task.status,
                'result': task.result,
                'progress': task.progress,
                'error_message': task.error_message,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            }
        )
    except Exception as e:
        logger.error(f"发送WebSocket更新失败: {str(e)}")

def process_debt_analysis(input_data, task):
    """
    处理债务分析任务
    """
    # 模拟处理过程
    update_task_progress(task, 25, "正在分析债务数据...")
    time.sleep(2)
    
    update_task_progress(task, 50, "正在计算最优还款策略...")
    time.sleep(2)
    
    update_task_progress(task, 75, "正在生成分析报告...")
    time.sleep(1)
    
    return "债务分析完成。根据您的财务状况，建议优先偿还高利率的信用卡债务，同时保持最低还款额以避免滞纳金。"

def process_payment_plan(input_data, task):
    """
    处理还款计划任务
    """
    # 模拟处理过程
    update_task_progress(task, 25, "正在评估您的收入和支出...")
    time.sleep(1)
    
    update_task_progress(task, 50, "正在制定个性化还款计划...")
    time.sleep(2)
    
    update_task_progress(task, 75, "正在优化还款策略...")
    time.sleep(1)
    
    return "还款计划已生成。建议您每月分配30%的收入用于债务偿还，优先处理利率最高的债务。"

def process_generic_task(input_data, task):
    """
    处理通用任务
    """
    # 模拟处理过程
    update_task_progress(task, 25, "正在处理请求...")
    time.sleep(1)
    
    update_task_progress(task, 50, "正在分析数据...")
    time.sleep(1)
    
    update_task_progress(task, 75, "正在生成结果...")
    time.sleep(1)
    
    return "任务处理完成。"

def update_task_progress(task, progress, message=""):
    """
    更新任务进度
    """
    task.progress = progress
    task.result = message
    task.save()
    
    # 这里可以添加发送实时更新到WebSocket的逻辑
    # 例如通过channel_layer发送消息