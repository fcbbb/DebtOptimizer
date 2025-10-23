from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'ai_agent'

urlpatterns = [
    path('api/tasks/', views.agent_task_list, name='agent_task_list'),
    path('api/tasks/create/', views.create_agent_task, name='create_agent_task'),
    path('api/tasks/<uuid:task_id>/', views.agent_task_detail, name='agent_task_detail'),
    path('api/tasks/<uuid:task_id>/status/', views.agent_task_status, name='agent_task_status'),
    path('api/upload-image/', views.upload_ai_image, name='upload_ai_image'),
    path('media/temp/<str:image_id>/', views.serve_temp_image, name='serve_temp_image'),
    path('websocket-test/', TemplateView.as_view(template_name='websocket_test.html'), name='websocket_test'),
]