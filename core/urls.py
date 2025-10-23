from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('clear-sessions/', views.clear_all_sessions, name='clear_sessions'),
    path('select-company/', views.select_company, name='select_company'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customer/create/', views.customer_create, name='customer_create'),
    path('customer/<int:customer_id>/', views.customer_detail, name='customer_detail'),
    path('customer/<int:customer_id>/update/', views.customer_update, name='customer_update'),
    path('customer/<int:customer_id>/delete/', views.customer_delete, name='customer_delete'),
    path('print/<int:customer_id>/', views.print_customer, name='print_customer'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('export/<int:customer_id>/', views.export_customer_excel, name='export_excel'),
    path('import-excel/', views.import_customer_excel, name='import_customer_excel'),
    path('temp/<str:filename>/', views.serve_temp_file, name='serve_temp_file'),
    # path('tasks/completed/', views.mark_tasks_completed, name='mark_tasks_completed'),
    path('customer/<int:customer_id>/toggle-status/', views.toggle_task_status, name='toggle_task_status'),
    path('customer/<int:customer_id>/contract-reminder/', views.mark_contract_reminder_processed, name='mark_contract_reminder_processed'),
    path('websocket-test/', TemplateView.as_view(template_name='websocket_test.html'), name='websocket_test'),
    
    # 图片上传和删除路由
    path('upload-customer-image/', views.upload_customer_image, name='upload_customer_image'),
    path('delete-customer-image/<int:image_id>/', views.delete_customer_image, name='delete_customer_image'),
    
    # 信用卡账单明细路由
    path('customer/<int:customer_id>/credit-card/create/', views.credit_card_create, name='credit_card_create'),
    path('credit-card/<int:credit_card_id>/update/', views.credit_card_update, name='credit_card_update'),
    path('credit-card/<int:credit_card_id>/delete/', views.credit_card_delete, name='credit_card_delete'),
    
    # 信用贷款账单明细路由
    path('customer/<int:customer_id>/loan/create/', views.loan_create, name='loan_create'),
    path('loan/<int:loan_id>/update/', views.loan_update, name='loan_update'),
    path('loan/<int:loan_id>/delete/', views.loan_delete, name='loan_delete'),
    
    # 月供出款记录路由
    path('customer/<int:customer_id>/monthly-payment/create/', views.monthly_payment_create, name='monthly_payment_create'),
    path('monthly-payment/<int:payment_id>/update/', views.monthly_payment_update, name='monthly_payment_update'),
    path('monthly-payment/<int:payment_id>/delete/', views.monthly_payment_delete, name='monthly_payment_delete'),
    
    # 信用卡出款记录路由
    path('customer/<int:customer_id>/credit-card-payment/create/', views.credit_card_payment_create, name='credit_card_payment_create'),
    path('credit-card-payment/<int:payment_id>/update/', views.credit_card_payment_update, name='credit_card_payment_update'),
    path('credit-card-payment/<int:payment_id>/delete/', views.credit_card_payment_delete, name='credit_card_payment_delete'),
    
    # 公司管理相关路由
    path('company/list/', views.company_list, name='company_list'),
    path('company/create/', views.company_create, name='company_create'),
    path('company/<int:company_id>/update/', views.company_update, name='company_update'),
    path('company/<int:company_id>/delete/', views.company_delete, name='company_delete'),
    
    # 归档客户列表
    path('archived-customers/', views.archived_customer_list, name='archived_customer_list'),
    
    # 归档客户
    path('customer/<int:customer_id>/archive/', views.archive_customer, name='archive_customer'),
    
    # 客服电话管理相关路由
    path('customer-service-phones/', views.customer_service_phone_list, name='customer_service_phone_list'),
    path('customer-service-phone/create/', views.customer_service_phone_create, name='customer_service_phone_create'),
    path('customer-service-phone/<int:phone_id>/update/', views.customer_service_phone_update, name='customer_service_phone_update'),
    path('customer-service-phone/<int:phone_id>/delete/', views.customer_service_phone_delete, name='customer_service_phone_delete'),
]