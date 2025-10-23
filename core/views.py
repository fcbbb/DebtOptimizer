from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta
from datetime import datetime
from decimal import Decimal
from .models import Customer, CreditCard, Loan, MonthlyPayment, CreditCardPayment, Company, CustomerServicePhone
from django.db import models
from .utils.excel_import import import_customer_from_excel
from .utils.excel_export import export_customer_to_excel
from .forms import ExcelImportForm
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from io import BytesIO
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Customer, CustomerImage
import urllib.parse
import tempfile
import webbrowser
import sys
import os


def index(request):
    """首页 - 显示明日提醒和统计"""
    
    # 获取选中的公司ID
    selected_company_id = request.session.get('selected_company_id')
    
    # 检查是否选择了归档客户公司，如果是则重定向到归档客户列表页面
    if selected_company_id:
        try:
            selected_company = Company.objects.get(id=selected_company_id)
            if selected_company.name == '归档客户':
                return redirect('core:archived_customer_list')
        except Company.DoesNotExist:
            pass
    
    # 获取明天的日期对象
    today = date.today()
    tomorrow = today + timedelta(days=1)
    tomorrow_day = tomorrow.day
    last_reset_date = request.session.get('last_reset_date')
    last_selected_company_id = request.session.get('last_selected_company_id')
    due_customers = Customer.objects.none()  # 空查询集
    # completed_customers = request.session.get('completed_customers', [])
    # 如果是新的一天，重置任务完成状态；如果是公司切换，保留该公司的完成状态
    if last_reset_date is None or last_reset_date != today.strftime('%Y-%m-%d'):
        # 新的一天，清空所有公司的完成状态
        request.session['completed_customers_by_company'] = {}
        
    # 计算工作日调整
    today_weekday = today.weekday()
    if today_weekday in [0, 1, 2, 3]:  # 今天是周一至周四
        # 处理明天的贷款
        adjusted_day = tomorrow_day
        # 分别跟踪信用卡客户和贷款客户
        credit_card_customer_ids = set()
        loan_customer_ids = set()
        
        # 处理信用卡客户
        due_cards_query = CreditCard.objects.filter( Q(repayment_date=adjusted_day) | Q(billing_date=adjusted_day)).exclude(customer__is_archived=True)
        # 应用公司过滤
        if selected_company_id:
            due_cards_query = due_cards_query.filter(customer__company_id=selected_company_id)
        due_cards = due_cards_query.select_related('customer')
        
        for card in due_cards:
            credit_card_customer_ids.add(card.customer.id)
        
        # 处理贷款客户并计算还款金额
        due_loans_query = Loan.objects.filter(repayment_date=adjusted_day).exclude(customer__is_archived=True)
        # 应用公司过滤
        if selected_company_id:
            due_loans_query = due_loans_query.filter(customer__company_id=selected_company_id)
        due_loans = due_loans_query.select_related('customer')
        
        for loan in due_loans:
            loan_customer_ids.add(loan.customer.id)
        
        # 合并所有需处理客户ID
        due_customer_ids = credit_card_customer_ids.union(loan_customer_ids)
        
        # 保存客户类型和还款金额到session
        request.session['credit_card_customer_ids'] = list(credit_card_customer_ids)
        request.session['loan_customer_ids'] = list(loan_customer_ids)
        # 获取需还款的客户列表
        due_customers = Customer.objects.filter(id__in=due_customer_ids)

    elif today_weekday == 4:  # 今天是周五
        # 处理周六、周日和下周一的贷款
        saturday = today + timedelta(days=1)
        sunday = today + timedelta(days=2)
        monday = today + timedelta(days=3)
        # 分别获取周六、周日和周一的贷款
        due_cards_query_sat = CreditCard.objects.filter( Q(repayment_date=saturday.day) | Q(billing_date=saturday.day)).exclude(customer__is_archived=True)
        due_cards_query_sun = CreditCard.objects.filter( Q(repayment_date=sunday.day) | Q(billing_date=sunday.day)).exclude(customer__is_archived=True)
        due_cards_query_mon = CreditCard.objects.filter( Q(repayment_date=monday.day) | Q(billing_date=monday.day)).exclude(customer__is_archived=True)
        
        # 应用公司过滤
        if selected_company_id:
            due_cards_query_sat = due_cards_query_sat.filter(customer__company_id=selected_company_id)
            due_cards_query_sun = due_cards_query_sun.filter(customer__company_id=selected_company_id)
            due_cards_query_mon = due_cards_query_mon.filter(customer__company_id=selected_company_id)
        
        due_cards_sat = due_cards_query_sat.select_related('customer')
        due_cards_sun = due_cards_query_sun.select_related('customer')
        due_cards_mon = due_cards_query_mon.select_related('customer')
        
        due_loans_query_sat = Loan.objects.filter(repayment_date=saturday.day).exclude(customer__is_archived=True)
        due_loans_query_sun = Loan.objects.filter(repayment_date=sunday.day).exclude(customer__is_archived=True)
        due_loans_query_mon = Loan.objects.filter(repayment_date=monday.day).exclude(customer__is_archived=True)
        
        # 应用公司过滤
        if selected_company_id:
            due_loans_query_sat = due_loans_query_sat.filter(customer__company_id=selected_company_id)
            due_loans_query_sun = due_loans_query_sun.filter(customer__company_id=selected_company_id)
            due_loans_query_mon = due_loans_query_mon.filter(customer__company_id=selected_company_id)
        
        due_loans_sat = due_loans_query_sat.select_related('customer')
        due_loans_sun = due_loans_query_sun.select_related('customer')
        due_loans_mon = due_loans_query_mon.select_related('customer')
        
        # 合并所有客户ID
        # 分别跟踪信用卡客户和贷款客户
        credit_card_customer_ids = set()
        loan_customer_ids = set()
        # 处理信用卡客户
        for card in due_cards_sat | due_cards_sun | due_cards_mon:
            credit_card_customer_ids.add(card.customer.id)
        # 处理贷款客户并计算还款金额
        for loan in due_loans_sat | due_loans_sun | due_loans_mon:
            loan_customer_ids.add(loan.customer.id)
        
        # 合并所有需处理客户ID
        due_customer_ids = credit_card_customer_ids.union(loan_customer_ids)
        
        # 保存客户类型和还款金额到session
        request.session['credit_card_customer_ids'] = list(credit_card_customer_ids)
        request.session['loan_customer_ids'] = list(loan_customer_ids)
        # 获取需还款的客户列表
        due_customers = Customer.objects.filter(id__in=due_customer_ids)

    else:  # 今天是周六或周日
        # 不处理任何贷款
        credit_card_customer_ids = set()
        loan_customer_ids = set()
        request.session['credit_card_customer_ids'] = list(credit_card_customer_ids)
        request.session['loan_customer_ids'] = list(loan_customer_ids)
        due_customers = Customer.objects.none()
    
    # 获取当前公司的完成状态
    completed_customers_by_company = request.session.get('completed_customers_by_company', {})
    company_key = str(selected_company_id or 'all')
    completed_customers = completed_customers_by_company.get(company_key, [])
    
    # 将due_customers按公司分组存储
    due_customers_by_company = request.session.get('due_customers_by_company', {})
    company_key = str(selected_company_id or 'all')
    due_customers_by_company[company_key] = list(due_customers.values('id', 'name', 'phone'))
    request.session['due_customers_by_company'] = due_customers_by_company
    request.session['last_reset_date'] = today.strftime('%Y-%m-%d')
    
    # 检查任务是否已完成（从session中获取当前公司的数据）
    due_customers = due_customers_by_company.get(company_key, [])
    due_customer_ids = set()
    for customer in due_customers:
        if isinstance(customer, dict) and 'id' in customer:
            due_customer_ids.add(customer['id'])
        elif hasattr(customer, 'get') and callable(getattr(customer, 'get')):
            due_customer_ids.add(customer.get('id'))
        else:
            due_customer_ids.add(customer)
    
    # 检查当前公司是否所有任务都已完成
    completed_customers_by_company = request.session.get('completed_customers_by_company', {})
    company_key = str(selected_company_id or 'all')
    completed_customers = completed_customers_by_company.get(company_key, [])
    
    # 过滤掉不再属于due_customers的已完成客户
    completed_customers = [int(cid) for cid in completed_customers if int(cid) in due_customer_ids]
    
    if bool(due_customer_ids and set(completed_customers) == due_customer_ids):
        tasks_completed = True
    elif not due_customer_ids:
        tasks_completed = True
    else:
        tasks_completed = False
    request.session['tasks_completed'] = tasks_completed

                    
    
    # 添加融资日期提醒 - 提前两个月
    financing_reminder_customers = Customer.objects.none()
    two_months_later = today + timedelta(days=70)
    # 基本查询集
    financing_query = Customer.objects.filter(financing_date__isnull=False).exclude(is_archived=True)
    # 应用公司过滤
    if selected_company_id:
        financing_query = financing_query.filter(company_id=selected_company_id)
    
    if financing_query.exists():
        financing_reminder_customers = financing_query.filter(
            financing_date__lte=two_months_later,
            financing_date__gte=today
        ).annotate(
            days_until_financing=models.F('financing_date') - models.Value(today, output_field=models.DateField())
        ).order_by('financing_date')

    # 保存融资提醒客户到session - 将date对象转换为字符串以支持JSON序列化
    financing_reminder_list = []
    for customer in financing_reminder_customers:
        customer_dict = {
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'financing_date': customer.financing_date.strftime('%Y-%m-%d') if customer.financing_date else None
        }
        financing_reminder_list.append(customer_dict)
    request.session['financing_reminder_customers'] = financing_reminder_list

    # 添加签约日期提醒 - 每35天提醒一次
    contract_reminder_customers = []
    contract_query = Customer.objects.filter(contract_date__isnull=False).exclude(is_archived=True)
    if selected_company_id:
        contract_query = contract_query.filter(company_id=selected_company_id)
    
    for customer in contract_query:
        days_since_contract = (today - customer.contract_date).days
        
        # 检查是否需要提醒（每35天提醒一次）
        if days_since_contract >= 0:
            # 计算基于签约日期的提醒基准
            if customer.last_reminder_date:
                # 已有提醒记录，按上次提醒时间计算
                days_since_last_reminder = (today - customer.last_reminder_date).days
                should_remind = days_since_last_reminder >= 35
            else:
                # 首次提醒，签约后35天开始
                days_since_last_reminder = days_since_contract  # 从签约开始计算
                should_remind = days_since_contract >= 35 and (days_since_contract % 35 == 0)
            
            if should_remind:
                # 计算这是第几次提醒（签约后每35天一次）
                reminder_count = (days_since_contract // 35)
                next_reminder_days = (reminder_count + 1) * 35
                next_reminder_date = customer.contract_date + timedelta(days=next_reminder_days)
                
                customer.days_since_contract = days_since_contract
                customer.next_reminder_days = next_reminder_days
                customer.next_reminder_date = next_reminder_date
                customer.reminder_count = reminder_count  # 第几次提醒
                contract_reminder_customers.append(customer)

    # 统计数据
    # 计算总客户数
    customer_query = Customer.objects.all().exclude(is_archived=True)
    # 应用公司过滤
    if selected_company_id:
        customer_query = customer_query.filter(company_id=selected_company_id)
    total_customers = customer_query.count()
    
    # 计算总出款
    payment_query = MonthlyPayment.objects.all().select_related('customer').exclude(customer__is_archived=True)
    # 应用公司过滤
    if selected_company_id:
        payment_query = payment_query.filter(customer__company_id=selected_company_id)
    total_payment = payment_query.aggregate(total=Sum('amount'))['total'] or 0
    
    # 计算总负债额度 = sum（贷款余额+信用卡余额）
    loan_query = Loan.objects.all().select_related('customer').exclude(customer__is_archived=True)
    # 应用公司过滤
    if selected_company_id:
        loan_query = loan_query.filter(customer__company_id=selected_company_id)
    total_debt_limit = loan_query.aggregate(total=Sum('balance'))['total'] or 0
    
    # 计算总月供 = sum（每月还款金额）
    total_monthly_payment = loan_query.aggregate(total=Sum('monthly_payment'))['total'] or 0

    # 保存当前选择的公司ID用于下次比较
    request.session['last_selected_company_id'] = selected_company_id

    # 获取当前公司的完成状态用于模板
    completed_customers_by_company = request.session.get('completed_customers_by_company', {})
    company_key = str(selected_company_id or 'all')
    completed_customers = completed_customers_by_company.get(company_key, [])
    
    # 获取签约提醒的处理状态
    completed_contract_customers_by_company = request.session.get('completed_contract_customers_by_company', {})
    completed_contract_customers = completed_contract_customers_by_company.get(company_key, [])
    
    # 计算签约提醒的完成状态
    contract_reminder_completed = False
    if contract_reminder_customers:
        # 获取需要提醒的客户ID列表
        reminder_customer_ids = [customer.id for customer in contract_reminder_customers]
        # 计算已处理的客户数量
        processed_count = len([cid for cid in reminder_customer_ids if cid in completed_contract_customers])
        # 只有当所有客户都处理完成时才标记为完成
        contract_reminder_completed = processed_count == len(reminder_customer_ids)
    
    context = {
        'due_customers': due_customers,
        'total_customers': total_customers,
        'total_monthly_payment': total_monthly_payment,
        'total_debt_limit': total_debt_limit,
        'total_payment': total_payment,
        'tasks_completed': tasks_completed,
        'today_date': today,
        'completed_customers': completed_customers,
        'completed_contract_customers': completed_contract_customers,
        'financing_reminder_customers': financing_reminder_customers,
        'contract_reminder_customers': contract_reminder_customers,
        'contract_reminder_completed': contract_reminder_completed,
        'credit_card_customer_ids': set(request.session.get('credit_card_customer_ids', [])),
        'loan_customer_ids': set(request.session.get('loan_customer_ids', [])),
    }
    return render(request, 'index.html', context)

def customer_list(request):
    """客户列表（含搜索和公司筛选）"""
    query = request.GET.get('q', '')  # 设置默认值为空字符串
    selected_company_id = request.session.get('selected_company_id')
    
    # 基本查询集
    if selected_company_id:
        # 获取选中的公司
        try:
            selected_company = Company.objects.get(id=selected_company_id)
            # 如果选择了归档客户公司，则只显示归档客户
            if selected_company.name == '归档客户':
                customers = Customer.objects.filter(is_archived=True, company=selected_company)
            else:
                # 对于其他公司，显示未归档的客户
                customers = Customer.objects.filter(company_id=selected_company_id, is_archived=False)
        except Company.DoesNotExist:
            customers = Customer.objects.none()
    else:
        # 没有选择公司时，显示所有未归档的客户
        customers = Customer.objects.filter(is_archived=False)

    # 应用搜索过滤
    if query:
        customers = customers.filter(
            models.Q(name__icontains=query) |
            models.Q(phone__icontains=query)
        )

    # 排序
    customers = customers.order_by('-created_at')

    return render(request, 'customer_list.html', {'customers': customers, 'query': query})

def clear_all_sessions(request):
    """清除所有session数据"""
    # 清除所有session数据
    request.session.flush()
    messages.success(request, '所有session数据已成功清除！')
    return redirect('core:index')

def select_company(request):
    """处理公司选择"""
    if request.method == 'POST':
        company_id = request.POST.get('company_id')
    else:  # GET请求
        company_id = request.GET.get('company_id')
    
    # 处理空字符串情况
    if company_id == '' or company_id is None:
        company_id = None
    
    # 存储选择的公司ID到session
    request.session['selected_company_id'] = company_id
    
    # 检查是否选择了归档客户公司
    if company_id:
        try:
            company = Company.objects.get(id=company_id)
            if company.name == '归档客户':
                # 如果选择了归档客户公司，重定向到归档客户列表页面
                messages.success(request, '已切换到归档客户')
                return redirect('core:archived_customer_list')
        except Company.DoesNotExist:
            pass
    
    # 清除相关缓存，确保切换公司后重新计算数据
    # 现在due_customers_by_company会自动处理，不需要手动清除
    # 注意：不要清除完成状态，让数据按公司维度保持独立
    
    messages.success(request, '公司选择已更新！')
    
    # 重定向回首页，确保重新计算
    return redirect('core:index')

def customer_create(request):
    """新增客户"""
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        notes = request.POST.get('notes')
        company_id = request.POST.get('company_id')
        
        # 获取倍率字段
        credit_card_multiplier = request.POST.get('credit_card_multiplier')
        monthly_payment_multiplier = request.POST.get('monthly_payment_multiplier')
        
        customer = Customer.objects.create(
            name=name,
            phone=phone,
            notes=notes,
            company_id=company_id if company_id else None,
            credit_card_multiplier=credit_card_multiplier if credit_card_multiplier else None,
            monthly_payment_multiplier=monthly_payment_multiplier if monthly_payment_multiplier else None
        )
        
        # 处理融资日期
        financing_date_str = request.POST.get('financing_date')
        if financing_date_str:
            from datetime import datetime
            customer.financing_date = datetime.strptime(financing_date_str, '%Y-%m-%d').date()
        
        # 处理签约日期
        contract_date_str = request.POST.get('contract_date')
        if contract_date_str:
            from datetime import datetime
            customer.contract_date = datetime.strptime(contract_date_str, '%Y-%m-%d').date()
            
        customer.save()
        messages.success(request, '客户创建成功！')
        return redirect('core:customer_detail', customer_id=customer.id)
    companies = Company.objects.exclude(name='归档客户').order_by('name')
    return render(request, 'customer_form.html', {'companies': companies})

def customer_update(request, customer_id):
    """编辑客户"""
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        customer.name = request.POST.get('name')
        customer.phone = request.POST.get('phone')
        customer.notes = request.POST.get('notes')
        
        # 处理倍率字段
        credit_card_multiplier = request.POST.get('credit_card_multiplier')
        monthly_payment_multiplier = request.POST.get('monthly_payment_multiplier')
        customer.credit_card_multiplier = credit_card_multiplier if credit_card_multiplier else None
        customer.monthly_payment_multiplier = monthly_payment_multiplier if monthly_payment_multiplier else None
        
        # 处理公司ID
        company_id = request.POST.get('company_id')
        customer.company_id = company_id if company_id else None
        
        # 处理融资日期
        financing_date_str = request.POST.get('financing_date')
        if financing_date_str:
            from datetime import datetime
            customer.financing_date = datetime.strptime(financing_date_str, '%Y-%m-%d').date()
        else:
            customer.financing_date = None
            
        # 处理签约日期
        contract_date_str = request.POST.get('contract_date')
        if contract_date_str:
            from datetime import datetime
            customer.contract_date = datetime.strptime(contract_date_str, '%Y-%m-%d').date()
        else:
            customer.contract_date = None
        
        customer.save()
        messages.success(request, '客户更新成功！')
        return redirect('core:customer_detail', customer_id=customer.id)
    companies = Company.objects.exclude(name='归档客户').order_by('name')
    return render(request, 'customer_form.html', {'customer': customer, 'companies': companies})

def customer_delete(request, customer_id):
    """删除客户"""
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, '客户删除成功！')
        return redirect('core:customer_list')
    return render(request, 'customer_confirm_delete.html', {'customer': customer})

def customer_detail(request, customer_id):
    """客户详情页（可编辑出款记录）"""
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        # 这里可以添加编辑逻辑
        messages.success(request, '数据已保存')
        return redirect('core:customer_detail', customer_id=customer_id)

    # 获取并排序信用卡账单：先按账单日排序，再按还款日排序
    credit_cards = customer.creditcard_set.all().order_by('billing_date', 'repayment_date')
    
    # 获取并排序贷款账单：按还款日排序
    loans = customer.loan_set.all().order_by('repayment_date')

    # 计算客户的资金使用成本和信用卡费率
    for payment in customer.monthlypayment_set.all():
        payment.calculate_cost()
        payment.save()

    for payment in customer.creditcardpayment_set.all():
        payment.calculate_fee()
        payment.save()
        
    # 计算单个客户的总负债
    total_debt = customer.total_debt

    # 计算单个客户的总出款
    total_payment = customer.total_payment
    # 计算单个客户的总月供
    total_monthly = customer.total_monthly_payment
    # 计算单个客户的总使用成本
    total_cost = 0
    for payment in customer.monthlypayment_set.all():
        # 确保成本已计算
        payment.calculate_cost()
        payment.save()
        total_cost += payment.cost
        
    # 计算总费用
    total_fee = total_cost + total_payment

    # 计算信用卡费率总和
    # 累加0账单费用总计（直接使用已计算的fee字段）
    total_credit_card_fee = 0
    for cp in customer.creditcardpayment_set.all():
        total_credit_card_fee += cp.fee

    # 计算融资日期剩余天数
    days_until_financing = None
    if customer.financing_date:
        today = date.today()
        days_until_financing = (customer.financing_date - today).days

    # 计算签约日期相关数据
    days_since_contract = None
    if customer.contract_date:
        today = date.today()
        days_since_contract = (today - customer.contract_date).days

    # 获取客户图片
    customer_images = customer.customerimage_set.all()
    
    # 判断今天需要还款的账单（用于高亮显示）
    # 获取明天的日期对象
    today = date.today()
    tomorrow = today + timedelta(days=1)
    tomorrow_day = tomorrow.day
    # 获取今天需要还款的信用卡账单ID
    # 信用卡账单需要区分账单日和还款日  
    due_credit_card_ids_repayment_date = set()
    due_credit_card_ids_billing_date = set()
    # 获取今天需要还款的贷款账单ID
    due_loan_ids = set()
    # 获取今天需要还款的信用卡账单银行和账单日信息
    due_credit_cards_info_repayment_date = []  # [{bank: ..., billing_date: ..., id: ...}, ...]
    due_credit_cards_info_billing_date = []  # [{bank: ..., billing_date: ..., id: ...}, ...]
        
    # 计算工作日调整
    today_weekday = today.weekday()
    if today_weekday in [0, 1, 2, 3]:  # 今天是周一至周四
        # 处理明天的贷款
        adjusted_day = tomorrow_day
        # 处理信用卡客户 - 使用已获取的credit_cards集合进行筛选
        for card in credit_cards:
            if card.repayment_date == adjusted_day:
                due_credit_card_ids_repayment_date.add(card.id)
                # 记录还款日是还款日的信用卡账单信息
                due_credit_cards_info_repayment_date.append({
                    'bank': card.bank,
                    'billing_date': card.repayment_date,
                    'id': card.id,
                })
            elif card.billing_date == adjusted_day:
                due_credit_card_ids_billing_date.add(card.id)
                # 记录账单日是还款日的信用卡账单信息
                due_credit_cards_info_billing_date.append({
                    'bank': card.bank,
                    'billing_date': card.billing_date,
                    'id': card.id,
                })
        # 处理贷款客户 - 使用已获取的loans集合进行筛选
        for loan in loans:
            if loan.repayment_date == adjusted_day:
                due_loan_ids.add(loan.id)

    elif today_weekday == 4:  # 今天是周五
        # 处理周六、周日和下周一的贷款
        saturday = today + timedelta(days=1)
        sunday = today + timedelta(days=2)
        monday = today + timedelta(days=3)
        # 使用已获取的credit_cards集合进行筛选
        for card in credit_cards:
            if (card.repayment_date == saturday.day or card.repayment_date == sunday.day or card.repayment_date == monday.day):
                due_credit_card_ids_repayment_date.add(card.id)
                # 记录还款日是还款日的信用卡账单信息
                due_credit_cards_info_repayment_date.append({
                    'bank': card.bank,
                    'billing_date': card.repayment_date,
                    'id': card.id,
                })
            elif (card.billing_date == saturday.day or card.billing_date == sunday.day or card.billing_date == monday.day): 
                due_credit_card_ids_billing_date.add(card.id)
                # 记录账单日是还款日的信用卡账单信息
                due_credit_cards_info_billing_date.append({
                    'bank': card.bank,
                    'billing_date': card.billing_date,
                    'id': card.id,
                })
        
        # 使用已获取的loans集合进行筛选
        for loan in loans:
            if loan.repayment_date == saturday.day or loan.repayment_date == sunday.day or loan.repayment_date == monday.day:
                due_loan_ids.add(loan.id)
        
    else:  # 今天是周六或周日
        # 周末不处理还款提醒
        due_loan_ids = set()
        due_credit_card_ids = set()
        

    context = {
        'customer': customer,
        'credit_cards': credit_cards,
        'loans': loans,
        'total_debt': total_debt,
        'total_payment': total_payment,
        'total_monthly': total_monthly,
        'total_cost': total_cost,
        'total_fee': total_fee,
        'days_until_financing': days_until_financing,
        'days_since_contract': days_since_contract,
        'total_credit_card_fee': total_credit_card_fee,
        'customer_images': customer_images,
        'due_credit_card_ids_repayment_date': due_credit_card_ids_repayment_date,
        'due_credit_card_ids_billing_date': due_credit_card_ids_billing_date,
        'due_loan_ids': due_loan_ids,
        'due_credit_cards_info_repayment_date': due_credit_cards_info_repayment_date,
        'due_credit_cards_info_billing_date': due_credit_cards_info_billing_date,
    }
    return render(request, 'customer_detail.html', context)

def print_customer(request, customer_id):
    """打印专用页面"""
    customer = get_object_or_404(Customer, id=customer_id)
    
    # 计算单个客户的总负债
    total_debt = customer.total_debt
    
    # 计算单个客户的总出款
    total_payment = customer.total_payment
    
    # 计算单个客户的总月供
    total_monthly = customer.total_monthly_payment
    
    # 计算单个客户的总使用成本
    total_cost = 0
    for payment in customer.monthlypayment_set.all():
        # 确保成本已计算
        payment.calculate_cost()
        payment.save()
        total_cost += payment.cost
        
    # 计算总费用
    total_fee = total_cost + total_payment
    
    # 累加0账单费用总计（直接使用已计算的fee字段）
    total_credit_card_fee = 0
    for cp in customer.creditcardpayment_set.all():
        total_credit_card_fee += cp.fee
        
    context = {
        'customer': customer,
        'total_debt': total_debt,
        'total_monthly': total_monthly,
        'total_payment': total_payment,
        'total_cost': total_cost,
        'total_fee': total_fee,
        'total_credit_card_fee': total_credit_card_fee,
        'now': timezone.now(),  # 添加当前时间变量
    }
    return render(request, 'print_customer.html', context)


def calendar_view(request):
    """还款日历视图"""
    today = date.today()
    # 获取选中的公司ID
    selected_company_id = request.session.get('selected_company_id')
    
    # 生成未来7天的日期列表
    dates = [today + timedelta(days=i) for i in range(7)]
    calendar_data = {}
    
    for d in dates:
        # 获取信用卡数据，应用公司筛选
        cards_query = CreditCard.objects.filter(
            Q(repayment_date=d.day) | Q(billing_date=d.day)
        ).select_related('customer')
        
        # 获取贷款数据，应用公司筛选
        loans_query = Loan.objects.filter(
            repayment_date=d.day
        ).select_related('customer')
        
        # 应用公司筛选
        if selected_company_id:
            cards_query = cards_query.filter(customer__company_id=selected_company_id)
            loans_query = loans_query.filter(customer__company_id=selected_company_id)
        
        cards = cards_query
        loans = loans_query
        
        calendar_data[d] = {'cards': cards, 'loans': loans}
    
    return render(request, 'calendar.html', {'calendar_data': calendar_data, 'dates': dates})

def toggle_task_status(request, customer_id):
    """切换客户的任务完成状态"""
    customer_id = int(customer_id)
    
    if request.method == 'POST':
        # 获取当前选择的公司ID
        selected_company_id = request.session.get('selected_company_id')
        company_key = str(selected_company_id or 'all')
        
        # 从session获取当前公司的需还款客户列表
        due_customers_by_company = request.session.get('due_customers_by_company', {})
        due_customers = due_customers_by_company.get(company_key, [])
        due_customer_ids = set()
        for customer in due_customers:
            if isinstance(customer, dict) and 'id' in customer:
                due_customer_ids.add(customer['id'])
            elif hasattr(customer, 'get') and callable(getattr(customer, 'get')):
                # 处理可能的QueryDict或其他类似dict的对象
                due_customer_ids.add(customer.get('id'))
            else:
                # 如果是整数ID直接添加
                due_customer_ids.add(customer)

        # 从session获取按公司存储的完成状态
        completed_customers_by_company = request.session.get('completed_customers_by_company', {})
        completed_customers = completed_customers_by_company.get(company_key, [])
        
        # 过滤掉不再属于due_customers的已完成客户
        completed_customers = [int(cid) for cid in completed_customers if int(cid) in due_customer_ids]

        # 切换当前客户的状态（仅当客户在due_customer_ids中时）
        is_completed = False  # 默认值为False
        if customer_id in due_customer_ids:
            if customer_id in completed_customers:
                completed_customers.remove(customer_id)
                is_completed = False
            else:
                completed_customers.append(customer_id)
                is_completed = True

        # 按公司更新完成状态
        completed_customers_by_company[company_key] = completed_customers
        request.session['completed_customers_by_company'] = completed_customers_by_company

        # 检查是否所有客户都已完成
        all_completed = bool(due_customer_ids and set(completed_customers) == due_customer_ids)
        
        # 获取首次完成标志（按公司存储）
        first_time_completed_by_company = request.session.get('first_time_completed_by_company', {})
        first_time_completed = first_time_completed_by_company.get(company_key, False)
        show_celebration = False

        if all_completed:
            request.session['tasks_completed'] = True
            # 如果是首次完成，设置庆祝标志
            if not first_time_completed:
                show_celebration = True
                first_time_completed_by_company[company_key] = True
                request.session['first_time_completed_by_company'] = first_time_completed_by_company
        else:
            request.session['tasks_completed'] = False
            # 未全部完成时，重置首次完成标志
            first_time_completed_by_company[company_key] = False
            request.session['first_time_completed_by_company'] = first_time_completed_by_company

        # 如果是AJAX请求，返回JSON响应
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'is_completed': is_completed,
                'all_completed': all_completed,
                'show_celebration': show_celebration,
                'completed_count': len(completed_customers),
                'total_count': len(due_customer_ids)
            })

        # 设置是否显示庆祝弹窗的标志
        request.session['show_celebration'] = show_celebration

    return redirect('core:index')

# 信用卡账单明细增删改查

def credit_card_create(request, customer_id):
    """添加信用卡账单"""
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        # 处理批量表单数据
        banks = request.POST.getlist('bank')
        total_limits = request.POST.getlist('total_limit')
        has_installment_list = request.POST.getlist('has_installment')
        installment_amounts = request.POST.getlist('installment_amount')
        billing_dates = request.POST.getlist('billing_date')
        repayment_dates = request.POST.getlist('repayment_date')
        
        # 创建计数器来跟踪成功创建的记录数
        created_count = 0
        
        # 遍历所有表单数据
        for i in range(len(banks)):
            # 获取当前表单项的数据
            bank = banks[i] if i < len(banks) else ''
            total_limit_str = total_limits[i] if i < len(total_limits) else '0'
            has_installment = 'has_installment' in request.POST.getlist('has_installment') if i < len(has_installment_list) else False
            installment_amount_str = installment_amounts[i] if i < len(installment_amounts) else '0'
            billing_date = billing_dates[i] if i < len(billing_dates) else None
            repayment_date = repayment_dates[i] if i < len(repayment_dates) else None
            
            # 只有当必要字段不为空时才创建记录
            if bank:
                # 处理数值字段
                total_limit = Decimal(total_limit_str or '0')
                installment_amount = Decimal(installment_amount_str or '0')
                
                # 创建记录
                CreditCard.objects.create(
                    customer=customer,
                    bank=bank,
                    total_limit=total_limit,
                    has_installment=has_installment,
                    installment_amount=installment_amount,
                    billing_date=billing_date,
                    repayment_date=repayment_date
                )
                created_count += 1
        
        messages.success(request, f'成功添加 {created_count} 条信用卡账单！')
        return redirect('core:customer_detail', customer_id=customer_id)
    return render(request, 'credit_card_form.html', {'customer': customer})

def credit_card_update(request, credit_card_id):
    """编辑信用卡账单"""
    credit_card = get_object_or_404(CreditCard, id=credit_card_id)
    if request.method == 'POST':
        credit_card.bank = request.POST.get('bank')
        # 处理数值字段，添加空值检查和类型转换
        total_limit_str = request.POST.get('total_limit', '').strip()
        credit_card.total_limit = Decimal(total_limit_str) if total_limit_str else Decimal('0')
        
        credit_card.has_installment = request.POST.get('has_installment') == 'on'
        
        installment_amount_str = request.POST.get('installment_amount', '').strip()
        credit_card.installment_amount = Decimal(installment_amount_str) if installment_amount_str else Decimal('0')
        
        # 处理整数字段
        billing_date = request.POST.get('billing_date')
        credit_card.billing_date = int(billing_date) if billing_date else 0
        
        repayment_date = request.POST.get('repayment_date')
        credit_card.repayment_date = int(repayment_date) if repayment_date else 0
        
        credit_card.save()
        messages.success(request, '信用卡账单更新成功！')
        return redirect('core:customer_detail', customer_id=credit_card.customer.id)
    return render(request, 'credit_card_update_form.html', {'credit_card': credit_card, 'customer': credit_card.customer})

def credit_card_delete(request, credit_card_id):
    """删除信用卡账单"""
    credit_card = get_object_or_404(CreditCard, id=credit_card_id)
    customer_id = credit_card.customer.id
    if request.method == 'POST':
        credit_card.delete()
        messages.success(request, '信用卡账单删除成功！')
        return redirect('core:customer_detail', customer_id=customer_id)
    return render(request, 'credit_card_confirm_delete.html', {'credit_card': credit_card, 'customer': credit_card.customer})

# 信用贷款账单明细增删改查

def loan_create(request, customer_id):
    """添加信用贷款账单"""
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        # 处理批量表单数据
        banks = request.POST.getlist('bank')
        total_limits = request.POST.getlist('total_limit')
        balances = request.POST.getlist('balance')
        monthly_payments = request.POST.getlist('monthly_payment')
        due_dates = request.POST.getlist('due_date')
        repayment_dates = request.POST.getlist('repayment_date')
        
        # 创建计数器来跟踪成功创建的记录数
        created_count = 0
        
        # 遍历所有表单数据
        for i in range(len(banks)):
            # 获取当前表单项的数据
            bank = banks[i] if i < len(banks) else ''
            total_limit_str = total_limits[i] if i < len(total_limits) else '0'
            balance_str = balances[i] if i < len(balances) else '0'
            monthly_payment_str = monthly_payments[i] if i < len(monthly_payments) else '0'
            due_date = due_dates[i] if i < len(due_dates) else None
            repayment_date = repayment_dates[i] if i < len(repayment_dates) else None
            
            # 只有当必要字段不为空时才创建记录
            if bank:
                # 处理数值字段
                total_limit = Decimal(total_limit_str or '0')
                balance = Decimal(balance_str or '0')
                monthly_payment = Decimal(monthly_payment_str or '0')
                
                # 创建记录
                Loan.objects.create(
                    customer=customer,
                    bank=bank,
                    total_limit=total_limit,
                    balance=balance,
                    monthly_payment=monthly_payment,
                    due_date=due_date,
                    repayment_date=repayment_date
                )
                created_count += 1
        
        messages.success(request, f'成功添加 {created_count} 条信用贷款账单！')
        return redirect('core:customer_detail', customer_id=customer_id)
    return render(request, 'loan_form.html', {'customer': customer})

def loan_update(request, loan_id):
    """编辑信用贷款账单"""
    loan = get_object_or_404(Loan, id=loan_id)
    if request.method == 'POST':
        loan.bank = request.POST.get('bank')
        # 处理数值字段，添加空值检查和类型转换
        total_limit_str = request.POST.get('total_limit', '').strip()
        loan.total_limit = Decimal(total_limit_str) if total_limit_str else Decimal('0')
        
        balance_str = request.POST.get('balance', '').strip()
        loan.balance = Decimal(balance_str) if balance_str else Decimal('0')
        
        monthly_payment_str = request.POST.get('monthly_payment', '').strip()
        loan.monthly_payment = Decimal(monthly_payment_str) if monthly_payment_str else Decimal('0')
        
        loan.due_date = request.POST.get('due_date')
        
        # 处理整数字段
        repayment_date = request.POST.get('repayment_date')
        loan.repayment_date = int(repayment_date) if repayment_date else 0
        
        loan.save()
        messages.success(request, '信用贷款账单更新成功！')
        return redirect('core:customer_detail', customer_id=loan.customer.id)
    return render(request, 'loan_update_form.html', {'loan': loan, 'customer': loan.customer})

def loan_delete(request, loan_id):
    """删除信用贷款账单"""
    loan = get_object_or_404(Loan, id=loan_id)
    customer_id = loan.customer.id
    if request.method == 'POST':
        loan.delete()
        messages.success(request, '信用贷款账单删除成功！')
        return redirect('core:customer_detail', customer_id)
    return render(request, 'loan_confirm_delete.html', {'loan': loan, 'customer': loan.customer})

# 月供出款记录增删改查

def monthly_payment_create(request, customer_id):
    """添加月供出款记录"""
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        # 处理批量表单数据
        payment_dates = request.POST.getlist('payment_date')
        amounts = request.POST.getlist('amount')
        notes_list = request.POST.getlist('notes')
        is_private_list = request.POST.getlist('is_private')
        
        # 创建计数器来跟踪成功创建的记录数
        created_count = 0
        
        # 遍历所有表单数据
        for i in range(len(payment_dates)):
            # 获取当前表单项的数据
            payment_date_str = payment_dates[i] if i < len(payment_dates) else None
            amount_str = amounts[i] if i < len(amounts) else '0'
            notes = notes_list[i] if i < len(notes_list) else ''
            is_private = 'is_private' in request.POST.getlist('is_private') if i < len(is_private_list) else False
            
            # 只有当必要字段不为空时才创建记录
            if payment_date_str:
                # 处理日期字段
                if payment_date_str:
                    payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
                else:
                    payment_date = None  # 或 date.today()
                    
                # 处理数值字段
                amount = Decimal(amount_str or '0')
                
                # 创建记录
                payment = MonthlyPayment.objects.create(
                    customer=customer,
                    payment_date=payment_date,
                    amount=amount,
                    notes=notes,
                    is_private=is_private
                )
                payment.calculate_cost()
                payment.save()
                created_count += 1
        
        messages.success(request, f'成功添加 {created_count} 条月供出款记录！')
        return redirect('core:customer_detail', customer_id=customer_id)
    return render(request, 'monthly_payment_form.html', {'customer': customer})

def monthly_payment_update(request, payment_id):
    """编辑月供出款记录"""
    payment = get_object_or_404(MonthlyPayment, id=payment_id)
    if request.method == 'POST':
        payment_date_str = request.POST.get('payment_date')
        if payment_date_str:
            payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
        else:
            # 处理空值情况，比如设为默认值或报错
            payment_date = None  # 或 date.today()
        payment.payment_date = payment_date
        payment.amount = Decimal(request.POST.get('amount') or '0')
        payment.notes = request.POST.get('notes')
        payment.is_private = request.POST.get('is_private') == 'on'
        payment.save()

        payment.calculate_cost()
        payment.save()
        messages.success(request, '月供出款记录更新成功！')
        return redirect('core:customer_detail', customer_id=payment.customer.id)
    return render(request, 'monthly_payment_update_form.html', {'payment': payment, 'customer': payment.customer})

def monthly_payment_delete(request, payment_id):
    """删除月供出款记录"""
    payment = get_object_or_404(MonthlyPayment, id=payment_id)
    customer_id = payment.customer.id
    if request.method == 'POST':
        payment.delete()
        messages.success(request, '月供出款记录删除成功！')
        return redirect('core:customer_detail', customer_id=customer_id)
    return render(request, 'monthly_payment_confirm_delete.html', {'payment': payment, 'customer': payment.customer})

# 信用卡出款记录增删改查

def credit_card_payment_create(request, customer_id):
    """添加信用卡出款记录"""
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        # 处理批量表单数据
        payment_dates = request.POST.getlist('payment_date')
        payment_amounts = request.POST.getlist('payment_amount')
        banks = request.POST.getlist('bank')
        withdrawal_amounts = request.POST.getlist('withdrawal_amount')
        withdrawal_dates = request.POST.getlist('withdrawal_date')
        notes_list = request.POST.getlist('notes')
        
        # 创建计数器来跟踪成功创建的记录数
        created_count = 0
        
        # 遍历所有表单数据
        for i in range(len(payment_dates)):
            # 获取当前表单项的数据
            payment_date_str = payment_dates[i] if i < len(payment_dates) else None
            payment_amount_str = payment_amounts[i] if i < len(payment_amounts) else '0'
            bank = banks[i] if i < len(banks) else ''
            withdrawal_amount_str = withdrawal_amounts[i] if i < len(withdrawal_amounts) else '0'
            withdrawal_date_str = withdrawal_dates[i] if i < len(withdrawal_dates) else None
            notes = notes_list[i] if i < len(notes_list) else ''
            
            # 只有当必要字段不为空时才创建记录
            if payment_date_str and bank:
                # 处理日期字段
                if payment_date_str:
                    payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
                else:
                    payment_date = None
                    
                # 处理数值字段
                payment_amount = Decimal(payment_amount_str or '0')
                withdrawal_amount = Decimal(withdrawal_amount_str or '0')
                
                # 创建记录
                payment = CreditCardPayment.objects.create(
                    customer=customer,
                    bank=bank,
                    payment_date=payment_date,
                    payment_amount=payment_amount,
                    withdrawal_amount=withdrawal_amount,
                    withdrawal_date=withdrawal_date_str if withdrawal_date_str else None,
                    notes=notes
                )
                payment.calculate_fee()
                payment.save()
                created_count += 1
        
        messages.success(request, f'成功添加 {created_count} 条信用卡出款记录！')
        return redirect('core:customer_detail', customer_id=customer_id)
    return render(request, 'credit_card_payment_form.html', {'customer': customer})

def credit_card_payment_update(request, payment_id):
    """编辑信用卡出款记录"""
    payment = get_object_or_404(CreditCardPayment, id=payment_id)
    if request.method == 'POST':
        payment.bank = request.POST.get('bank')
        payment_date = request.POST.get('payment_date')
        if payment_date:
            payment.payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
        else:
            payment.payment_date = None
        payment.payment_amount = Decimal(request.POST.get('payment_amount') or '0')
        payment.withdrawal_amount = Decimal(request.POST.get('withdrawal_amount') or '0')
        withdrawal_date = request.POST.get('withdrawal_date')
        if withdrawal_date:
            payment.withdrawal_date = datetime.strptime(withdrawal_date, '%Y-%m-%d').date()
        else:
            payment.withdrawal_date = None
        payment.notes = request.POST.get('notes')
        payment.save()
        payment.calculate_fee()
        payment.save()
        messages.success(request, '信用卡出款记录更新成功！')
        return redirect('core:customer_detail', customer_id=payment.customer.id)
    return render(request, 'credit_card_payment_update_form.html', {'payment': payment, 'customer': payment.customer})

def credit_card_payment_delete(request, payment_id):
    """删除信用卡出款记录"""
    payment = get_object_or_404(CreditCardPayment, id=payment_id)
    customer_id = payment.customer.id
    if request.method == 'POST':
        payment.delete()
        messages.success(request, '信用卡出款记录删除成功！')
        return redirect('core:customer_detail', customer_id=customer_id)
    return render(request, 'credit_card_payment_confirm_delete.html', {'payment': payment, 'customer': payment.customer})


# 公司管理相关视图
def company_list(request):
    """公司列表"""
    companies = Company.objects.all().order_by('created_at')
    return render(request, 'company_list.html', {'companies': companies})

def company_create(request):
    """创建公司"""
    if request.method == 'POST':
        name = request.POST.get('name')
        Company.objects.create(name=name)
        messages.success(request, '公司创建成功！')
        return redirect('core:company_list')
    return render(request, 'company_form.html')

def company_update(request, company_id):
    """更新公司"""
    company = get_object_or_404(Company, id=company_id)
    if request.method == 'POST':
        company.name = request.POST.get('name')
        company.save()
        messages.success(request, '公司更新成功！')
        return redirect('core:company_list')
    return render(request, 'company_form.html', {'company': company})

def company_delete(request, company_id):
    """删除公司"""
    company = get_object_or_404(Company, id=company_id)
    if request.method == 'POST':
        company.delete()
        messages.success(request, '公司删除成功！')
        return redirect('core:company_list')
    return render(request, 'company_confirm_delete.html', {'company': company})
    

def export_customer_excel(request, customer_id):
    """导出客户数据为Excel"""
    customer = get_object_or_404(Customer, id=customer_id)
    wb = export_customer_to_excel(customer)
    
    # 检查是否在PyInstaller打包的桌面环境中运行
    if getattr(sys, 'frozen', False):
        # 在桌面环境中，使用更安全的方式处理文件下载
        try:
            # 使用应用目录下的临时文件夹，避免系统临时目录的权限问题
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller运行时环境
                temp_dir = os.path.join(os.path.dirname(sys.executable), 'temp')
            else:
                # 开发环境
                temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
            
            # 确保临时目录存在
            os.makedirs(temp_dir, exist_ok=True)
            
            # 生成文件名
            filename = f"{customer.name}_债务信息_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            file_path = os.path.join(temp_dir, filename)
            
            # 保存Excel文件
            wb.save(file_path)
            
            # 显示弹窗通知用户下载完成
            try:
                if sys.platform == "win32":
                    # Windows系统弹窗
                    import ctypes
                    msg = f"Excel文件已成功生成并下载到以下位置:\n\n{file_path}\n\n点击确定后将尝试自动打开文件。"
                    title = "下载完成"
                    ctypes.windll.user32.MessageBoxW(0, msg, title, 0x40)
                    # 尝试打开文件
                    os.startfile(file_path)
                elif sys.platform == "darwin":
                    # macOS系统通知
                    os.system(f"osascript -e 'display notification \"Excel文件已成功生成并下载: {file_path}\" with title \"下载完成\"'")
                    os.system(f"open '{file_path}'")
                else:
                    # Linux系统通知
                    os.system(f'notify-send "下载完成" "Excel文件已成功生成并下载: {file_path}"')
                    os.system(f"xdg-open '{file_path}'")
            except Exception as e:
                # 如果系统通知失败，不影响主要功能
                pass
            
            # # 提供明确的成功消息
            # messages.success(request, f'Excel文件已成功生成并下载:<br><strong>{file_path}</strong><br>'
            #                  f'文件已自动下载到您的浏览器中。如果下载未自动开始，请复制上述路径到文件管理器中打开。<br>'
            #                  f'<a href="{reverse("core:serve_temp_file", kwargs={"filename": filename})}" class="btn btn-primary mt-2" download>点击此处下载文件</a>')
            
            # 返回文件下载响应而不是简单的文本
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                encoded_filename = urllib.parse.quote(filename)
                response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
                # 尝试删除已发送的文件，减少磁盘占用
                try:
                    os.remove(file_path)
                except:
                    pass  # 如果删除失败，不影响用户下载
                return response
        except PermissionError:
            # 如果遇到权限问题，回退到内存缓冲区方式
            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)
            
            response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            filename = f"{customer.name}_债务信息_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            encoded_filename = urllib.parse.quote(filename)
            response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            
            # 提供明确的成功消息
            messages.success(request, f'Excel文件已成功生成并下载:文件已自动下载到您的浏览器中。')
            return response
        except Exception as e:
            # 其他异常也回退到内存缓冲区方式
            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)
            
            response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            filename = f"{customer.name}_债务信息_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            encoded_filename = urllib.parse.quote(filename)
            response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            
            # 提供明确的成功消息
            messages.success(request, f'Excel文件已成功生成并下载:文件已自动下载到您的浏览器中。')
            return response
    else:
        # 在Web环境中，使用原来的HttpResponse方式
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f"{customer.name}_债务信息_{timezone.now().strftime('%Y%m%d')}.xlsx"
        encoded_filename = urllib.parse.quote(filename)
        response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
        return response


@require_http_methods(["POST"])
def upload_customer_image(request):
    """上传客户图片（支持单张和批量上传）"""
    try:
        customer_id = request.POST.get('customer_id')
        customer = get_object_or_404(Customer, id=customer_id)
        
        # 检查是否是批量上传
        image_files = request.FILES.getlist('images')
        
        if image_files:
            # 批量上传处理
            uploaded_images = []
            
            for image_file in image_files:
                # 使用图片文件名作为标题（去掉扩展名）
                title = os.path.splitext(image_file.name)[0]
                
                # 创建CustomerImage实例
                customer_image = CustomerImage(
                    customer=customer,
                    title=title,
                    image=image_file
                )
                customer_image.save()
                
                # 收集上传的图片信息
                image_data = {
                    'id': customer_image.id,
                    'title': customer_image.title,
                    'url': customer_image.image.url,
                    'uploaded_at': customer_image.uploaded_at.strftime('%Y-%m-%d %H:%M')
                }
                uploaded_images.append(image_data)
            
            return JsonResponse({'success': True, 'message': f'成功批量上传 {len(uploaded_images)} 张图片', 'images': uploaded_images})
        
        else:
            # 单张上传处理
            image_file = request.FILES.get('image')
            if not image_file:
                return JsonResponse({'success': False, 'error': '未选择图片文件'})
            
            # 获取图片标题
            title = request.POST.get('title', '').strip()
            
            # 如果用户没有输入标题，则使用图片文件名作为标题（去掉扩展名）
            if not title:
                title = os.path.splitext(image_file.name)[0]
            
            # 创建CustomerImage实例
            customer_image = CustomerImage(
                customer=customer,
                title=title,
                image=image_file
            )
            customer_image.save()
            
            # 返回新上传图片的详细信息，以便前端可以动态添加
            image_data = {
                'id': customer_image.id,
                'title': customer_image.title,
                'url': customer_image.image.url,
                'uploaded_at': customer_image.uploaded_at.strftime('%Y-%m-%d %H:%M')
            }
            
            return JsonResponse({'success': True, 'message': '图片上传成功', 'image': image_data})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(["POST"])
def delete_customer_image(request, image_id):
    """删除客户图片"""
    try:
        image = get_object_or_404(CustomerImage, id=image_id)
        # 删除图片文件
        image.image.delete()
        # 删除数据库记录
        image.delete()
        
        return JsonResponse({'success': True, 'message': '图片删除成功'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def import_customer_excel(request):
    """从Excel导入客户数据"""
    if request.method == 'POST':
        form = ExcelImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            
            try:
                # 获取当前选择的公司
                selected_company_id = request.session.get('selected_company_id')
                if not selected_company_id:
                    messages.error(request, '请先选择一个公司再进行导入操作')
                    return redirect('core:import_customer_excel')
                
                try:
                    company = Company.objects.get(id=selected_company_id)
                except Company.DoesNotExist:
                    messages.error(request, '选择的公司不存在')
                    return redirect('core:import_customer_excel')
                
                customer, error = import_customer_from_excel(file, company)
                if error:
                    messages.error(request, f'导入失败: {error}')
                    return redirect('core:import_customer_excel')
                
                messages.success(request, f'成功导入客户: {customer.name}')
                return redirect('core:customer_detail', customer_id=customer.id)
                    
            except Exception as e:
                messages.error(request, f'导入过程中发生错误: {str(e)}')
                return redirect('core:import_customer_excel')
    else:
        form = ExcelImportForm()
    
    return render(request, 'import_excel.html', {'form': form})

def mark_contract_reminder_processed(request, customer_id):
    """标记签约提醒为已处理"""
    if request.method == 'POST':
        try:
            customer = get_object_or_404(Customer, id=customer_id)
            customer.last_reminder_date = date.today()
            customer.save()
            
            # 更新处理状态到session
            selected_company_id = request.session.get('selected_company_id')
            company_key = str(selected_company_id or 'all')
            
            completed_contract_customers_by_company = request.session.get('completed_contract_customers_by_company', {})
            if company_key not in completed_contract_customers_by_company:
                completed_contract_customers_by_company[company_key] = []
            
            if customer_id not in completed_contract_customers_by_company[company_key]:
                completed_contract_customers_by_company[company_key].append(customer_id)
            
            request.session['completed_contract_customers_by_company'] = completed_contract_customers_by_company
            
            # 检查是否所有客户都已处理完成
            selected_company_id = request.session.get('selected_company_id')
            company_key = str(selected_company_id or 'all')
            completed_contract_customers_by_company = request.session.get('completed_contract_customers_by_company', {})
            processed_customer_ids = completed_contract_customers_by_company.get(company_key, [])
            
            # 获取当前公司需要提醒的客户
            from django.utils import timezone
            from datetime import timedelta
            
            today = timezone.now().date()
            reminder_customers = Customer.objects.filter(
                company_id=selected_company_id if selected_company_id else None,
                contract_date__isnull=False
            ).filter(
                models.Q(last_reminder_date__isnull=True) |
                models.Q(last_reminder_date__lt=today - timedelta(days=35))
            )
            
            # 获取所有需要提醒的客户ID
            reminder_customer_ids = list(reminder_customers.values_list('id', flat=True))
            
            # 检查是否所有需要提醒的客户都已处理
            all_processed = all(cid in processed_customer_ids for cid in reminder_customer_ids)
            all_completed = all_processed and len(reminder_customer_ids) > 0
            
            return JsonResponse({'success': True, 'all_completed': all_completed})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


def serve_temp_file(request, filename):
    """提供临时文件访问"""
    # 构建文件路径
    if getattr(sys, 'frozen', False):
        # PyInstaller环境
        temp_dir = os.path.join(os.path.dirname(sys.executable), 'temp')
    else:
        # 开发环境
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
    
    file_path = os.path.join(temp_dir, filename)
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise Http404("文件不存在")
    
    # 返回文件响应
    response = FileResponse(open(file_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def archived_customer_list(request):
    """归档客户列表"""
    query = request.GET.get('q', '')  # 设置默认值为空字符串
    
    # 获取归档客户公司
    try:
        archived_company = Company.objects.get(name='归档客户')
    except Company.DoesNotExist:
        # 如果归档客户公司不存在，则创建它
        archived_company = Company.objects.create(name='归档客户')
    
    # 查询归档客户
    customers = Customer.objects.filter(is_archived=True, company=archived_company)

    # 应用搜索过滤
    if query:
        customers = customers.filter(
            models.Q(name__icontains=query) |
            models.Q(phone__icontains=query)
        )

    # 排序
    customers = customers.order_by('-created_at')

    return render(request, 'archived_customer_list.html', {'customers': customers, 'query': query})


def customer_service_phone_list(request):
    """客服电话列表"""
    query = request.GET.get('q', '')  # 获取搜索关键词
    
    # 基本查询集
    phones = CustomerServicePhone.objects.all().order_by('bank_name')
    
    # 应用搜索过滤
    if query:
        phones = phones.filter(
            models.Q(bank_name__icontains=query) |
            models.Q(phone_number__icontains=query)
        )
    
    return render(request, 'customer_service_phone_list.html', {'phones': phones, 'query': query})


def customer_service_phone_create(request):
    """创建客服电话"""
    if request.method == 'POST':
        bank_name = request.POST.get('bank_name')
        phone_number = request.POST.get('phone_number')
        CustomerServicePhone.objects.create(bank_name=bank_name, phone_number=phone_number)
        messages.success(request, '客服电话创建成功！')
        return redirect('core:customer_service_phone_list')
    return render(request, 'customer_service_phone_form.html')


def customer_service_phone_update(request, phone_id):
    """更新客服电话"""
    phone = get_object_or_404(CustomerServicePhone, id=phone_id)
    if request.method == 'POST':
        phone.bank_name = request.POST.get('bank_name')
        phone.phone_number = request.POST.get('phone_number')
        phone.save()
        messages.success(request, '客服电话更新成功！')
        return redirect('core:customer_service_phone_list')
    return render(request, 'customer_service_phone_form.html', {'phone': phone})


def customer_service_phone_delete(request, phone_id):
    """删除客服电话"""
    phone = get_object_or_404(CustomerServicePhone, id=phone_id)
    if request.method == 'POST':
        phone.delete()
        messages.success(request, '客服电话删除成功！')
        return redirect('core:customer_service_phone_list')
    return render(request, 'customer_service_phone_confirm_delete.html', {'phone': phone})


def archive_customer(request, customer_id):
    """归档客户"""
    if request.method == 'POST':
        customer = get_object_or_404(Customer, id=customer_id)
        
        # 获取归档客户公司
        try:
            archived_company = Company.objects.get(name='归档客户')
        except Company.DoesNotExist:
            # 如果归档客户公司不存在，则创建它
            archived_company = Company.objects.create(name='归档客户')
        
        # 将客户移到归档客户公司并设置为已归档
        customer.company = archived_company
        customer.is_archived = True
        customer.save()
        
        messages.success(request, f'客户 {customer.name} 已成功归档')
        return redirect('core:customer_detail', customer_id=customer.id)
    
    return redirect('core:customer_list')