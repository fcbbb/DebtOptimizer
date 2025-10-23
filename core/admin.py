# core/admin.py
from django.contrib import admin
from django import forms
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect  # 添加这一行
from django.urls import path
from django.utils.html import format_html
from django.contrib import messages
from .models import Customer, CreditCard, Loan, MonthlyPayment, CreditCardPayment, Company, CustomerServicePhone
from .utils.excel_import import import_customer_from_excel


# --- 自定义文件上传表单 ---
class ExcelImportForm(forms.Form):
    excel_file = forms.FileField(
        label='选择 Excel 文件',
        help_text='上传符合模板格式的 .xlsx 或 .xls 文件',
        widget=forms.FileInput(attrs={'accept': '.xlsx,.xls'})
    )

# --- CustomerAdmin ---
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'company', 'created_at']
    search_fields = ['name', 'phone', 'company__name']
    list_filter = ['created_at', 'company']
    ordering = ['-created_at']
    list_per_page = 20

    # --- 添加自定义 URL ---
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # 这个 URL 是独立的，不依赖于任何对象
            path('import-excel/', self.admin_site.admin_view(self.import_excel_view), name='import_excel'),
        ]
        return custom_urls + urls

    # --- 导入视图 ---
    def import_excel_view(self, request):
        if request.method == "POST":
            form = ExcelImportForm(request.POST, request.FILES)
            if form.is_valid():
                excel_file = request.FILES['excel_file']
                
                if not excel_file.name.endswith(('.xlsx', '.xls')):
                    messages.error(request, '请上传有效的 Excel 文件 (.xlsx 或 .xls)')
                else:
                    try:
                        # 获取当前选择的公司
                        selected_company_id = request.session.get('selected_company_id')
                        if not selected_company_id:
                            messages.error(request, '请先选择一个公司再进行导入操作')
                            return HttpResponseRedirect("../../")
                        
                        try:
                            company = Company.objects.get(id=selected_company_id)
                        except Company.DoesNotExist:
                            messages.error(request, '选择的公司不存在')
                            return HttpResponseRedirect("../../")
                        
                        customer, error = import_customer_from_excel(excel_file, company)
                        if error:
                            messages.error(request, f'导入失败：{error}')
                        else:
                            messages.success(request, f'客户 "{customer.name}" 导入成功！')
                            # 成功后重定向回客户列表
                            return HttpResponseRedirect("../../")
                    except Exception as e:
                        messages.error(request, f'导入过程中发生未知错误：{str(e)}')
        else:
            form = ExcelImportForm()

        context = {
            'title': '从 Excel 导入客户信息',
            'form': form,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
            'media': self.media,
        }
        return render(request, 'import_excel.html', context)

@admin.register(CreditCard)
class CreditCardAdmin(admin.ModelAdmin):
    list_display = ['customer', 'bank', 'total_limit', 'repayment_date', 'has_installment']
    list_filter = ['customer', 'bank', 'has_installment', 'repayment_date']
    search_fields = ['customer__name', 'bank']
    list_per_page = 20

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['customer', 'bank', 'total_limit', 'balance', 'monthly_payment', 'repayment_date']
    list_filter = ['customer', 'bank', 'repayment_date']
    search_fields = ['customer__name', 'bank']
    list_per_page = 20

@admin.register(MonthlyPayment)
class MonthlyPaymentAdmin(admin.ModelAdmin):
    list_display = ['customer', 'payment_date', 'amount', 'notes']
    list_filter = ['customer', 'payment_date']
    search_fields = ['customer__name', 'notes']
    list_per_page = 20

@admin.register(CreditCardPayment)
class CreditCardPaymentAdmin(admin.ModelAdmin):
    list_display = ['customer', 'bank', 'payment_date', 'payment_amount', 'withdrawal_amount', 'withdrawal_date']
    list_filter = ['customer', 'bank', 'payment_date', 'withdrawal_date']
    search_fields = ['customer__name', 'bank']
    list_per_page = 20

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']
    ordering = ['-created_at']
    list_per_page = 20


@admin.register(CustomerServicePhone)
class CustomerServicePhoneAdmin(admin.ModelAdmin):
    list_display = ['bank_name', 'phone_number', 'created_at', 'updated_at']
    search_fields = ['bank_name', 'phone_number']
    list_filter = ['created_at', 'updated_at']
    ordering = ['bank_name']
    list_per_page = 20