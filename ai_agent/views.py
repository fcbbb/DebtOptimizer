from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import AgentTask
from .serializers import AgentTaskSerializer, AgentTaskCreateSerializer
from .tasks import process_agent_task
import logging
import uuid
import json
import base64
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .temp_storage import save_temp_image, get_temp_image, delete_temp_image

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_task_list(request):
    """
    获取当前用户的所有AI代理任务
    """
    tasks = AgentTask.objects.filter(user=request.user).order_by('-created_at')
    serializer = AgentTaskSerializer(tasks, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_task_detail(request, task_id):
    """
    获取特定AI代理任务的详细信息
    """
    try:
        task = AgentTask.objects.get(id=task_id, user=request.user)
    except AgentTask.DoesNotExist:
        return Response({'error': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = AgentTaskSerializer(task)
    return Response(serializer.data)

@api_view(['POST'])
# @permission_classes([IsAuthenticated])  # 暂时移除认证要求以便测试
def create_agent_task(request):
    """
    创建新的AI代理任务
    """
    # 手动创建一个用户用于测试
    from django.contrib.auth.models import User
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        # 创建或获取一个测试用户
        user, created = User.objects.get_or_create(username='testuser')
        request.user = user
    
    serializer = AgentTaskCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        task = serializer.save()
        
        # 异步启动Celery任务
        process_agent_task.delay(str(task.id))
        
        # 返回创建的任务信息
        response_serializer = AgentTaskSerializer(task)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_task_status(request, task_id):
    """
    获取AI代理任务的当前状态
    """
    try:
        task = AgentTask.objects.get(id=task_id, user=request.user)
    except AgentTask.DoesNotExist:
        return Response({'error': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'id': str(task.id),
        'status': task.status,
        'progress': task.progress,
        'result': task.result,
        'error_message': task.error_message,
        'updated_at': task.updated_at
    })

@api_view(['POST'])
@permission_classes([])  # 移除所有权限要求
@csrf_exempt
def upload_ai_image(request):
    """
    处理AI聊天界面图片上传
    """
    try:
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({'error': 'No image provided'}, status=400)
        
        # 生成唯一的图片ID
        image_id = f"temp_{uuid.uuid4().hex}"
        
        # 读取图片数据
        image_bytes = image_file.read()
        
        # 保存到临时存储
        from .temp_storage import save_temp_image
        save_temp_image(image_id, image_bytes)
        
        return Response({'image_id': image_id})
    except Exception as e:
        return Response({'error': str(e)}, status=500)

def serve_temp_image(request, image_id):
    # 从临时存储获取图片数据
    image_data = get_temp_image(image_id)
    
    if image_data is None:
        return HttpResponse('图片未找到', status=404)
    
    # 确定内容类型（简化处理，实际项目中可能需要根据文件头判断）
    content_type = 'image/jpeg'  # 默认JPEG
    
    # 简单的图片类型检测
    if image_data.startswith(b'\x89PNG\r\n\x1a\n'):
        content_type = 'image/png'
    elif image_data.startswith(b'\xff\xd8\xff'):
        content_type = 'image/jpeg'
    elif image_data.startswith(b'GIF87a') or image_data.startswith(b'GIF89a'):
        content_type = 'image/gif'
    
    # 返回图片数据
    return HttpResponse(image_data, content_type=content_type)

def websocket_test(request):
    """
    WebSocket测试页面
    """
    return render(request, 'websocket_test.html')
