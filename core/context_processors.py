# core/context_processors.py
from .models import Company


def company_context(request):
    """提供公司列表和当前选择的公司ID"""
    # 获取所有公司，按创建时间排序
    all_companies = Company.objects.all().order_by('created_at')
    
    # 分离归档客户和其他公司
    archived_company = None
    other_companies = []
    
    for company in all_companies:
        if company.name == '归档客户':
            archived_company = company
        else:
            other_companies.append(company)
    
    # 将归档客户放在最后
    companies = other_companies + ([archived_company] if archived_company else [])
    
    selected_company_id = request.session.get('selected_company_id')
    
    # 特殊处理：如果当前访问的是归档客户列表页面，且session中没有selected_company_id，则设置selected_company_id为归档客户的ID
    if request.resolver_match and request.resolver_match.url_name == 'archived_customer_list':
        if archived_company and not selected_company_id:
            selected_company_id = archived_company.id
    
    # 将selected_company_id转换为整数类型（如果存在且不为空）
    if selected_company_id is not None and selected_company_id != '':
        try:
            selected_company_id = int(selected_company_id)
        except (ValueError, TypeError):
            selected_company_id = None
    else:
        selected_company_id = None
    
    return {
        'companies': companies,
        'selected_company_id': selected_company_id,
    }