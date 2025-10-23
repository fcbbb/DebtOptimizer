# core/models.py
from django.db import models
from django.contrib import admin

class Company(models.Model):
    name = models.CharField("公司名称", max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "公司"
        verbose_name_plural = "公司"

class Customer(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="所属公司", null=True, blank=True)
    name = models.CharField("客户姓名", max_length=100)
    phone = models.CharField("电话及微信号", max_length=50, blank=True)
    notes = models.TextField("备注", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    financing_date = models.DateField("融资日期", null=True, blank=True)
    contract_date = models.DateField("签约日期", null=True, blank=True)
    last_reminder_date = models.DateField("上一次提醒日期", null=True, blank=True)
    credit_card_multiplier = models.DecimalField("信用卡倍率", max_digits=5, decimal_places=2, default=0.03, null=True, blank=True)
    monthly_payment_multiplier = models.DecimalField("月供倍率", max_digits=5, decimal_places=3, default=0.002, null=True, blank=True)
    is_archived = models.BooleanField("是否已归档", default=False)

    def __str__(self):
        return self.name
        
    @property
    def total_debt(self):
        # 总负债 = 所有贷款余额
        loan_balance = sum(loan.balance or 0 for loan in self.loan_set.all()) if self.loan_set.all() else 0
        # credit_card_limit = sum(card.total_limit or 0 for card in self.creditcard_set.all()) if self.creditcard_set.all() else 0
        return loan_balance
        
    @property
    def total_monthly_payment(self):
        # 总月供 = 所有贷款月还款
        loan_monthly = sum(loan.monthly_payment or 0 for loan in self.loan_set.all()) if self.loan_set.all() else 0 
        # monthly_payments = sum(payment.amount or 0 for payment in self.monthlypayment_set.all()) if self.monthlypayment_set.all() else 0
        return loan_monthly
        
    @property
    def total_payment(self):
        # 总出款 = 所有月供出款记录金额
        monthly_payments = sum(payment.amount or 0 for payment in self.monthlypayment_set.all()) if self.monthlypayment_set.all() else 0
        # credit_card_payments = sum(payment.payment_amount or 0 for payment in self.creditcardpayment_set.all()) if self.creditcardpayment_set.all() else 0
        return monthly_payments

    class Meta:
        verbose_name = "客户"
        verbose_name_plural = "客户"

class CreditCard(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="客户")
    bank = models.CharField("银行渠道", max_length=50)
    total_limit = models.DecimalField("总授信额度", max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    has_installment = models.BooleanField("有无分期", default=False)
    installment_amount = models.DecimalField("分期金额", max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    billing_date = models.PositiveSmallIntegerField("账单日", null=True, blank=True)
    repayment_date = models.PositiveSmallIntegerField("还款日", null=True, blank=True)

    class Meta:
        verbose_name = "信用卡账单明细"
        verbose_name_plural = "信用卡账单明细"

class Loan(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="客户")
    bank = models.CharField("银行渠道", max_length=50)
    total_limit = models.DecimalField("总授信额度", max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    balance = models.DecimalField("贷款余额", max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    monthly_payment = models.DecimalField("月还款", max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    due_date = models.DateField("到期时间", null=True, blank=True)
    repayment_date = models.PositiveSmallIntegerField("还款日", null=True, blank=True)

    class Meta:
        verbose_name = "信用贷款账单明细"
        verbose_name_plural = "信用贷款账单明细"

class MonthlyPayment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="客户")
    payment_date = models.DateField("出款时间")
    amount = models.DecimalField("出款金额", max_digits=12, decimal_places=2, null=True,blank=True)
    notes = models.CharField("备注", max_length=200, blank=True)
    is_private = models.BooleanField("是否私人借款", default=False)
    cost = models.DecimalField("资金使用成本", max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    days_used = models.PositiveIntegerField("资金使用天数", default=0, null=True, blank=True)

    def calculate_cost(self):
        from datetime import date
        from decimal import Decimal
        today = date.today()
        if self.payment_date:
            self.days_used = (today - self.payment_date).days + 1
            if(self.days_used < 0):
                self.days_used = 0

        else:
            self.days_used = 0
            
        # 如果是私人借款，使用0.003的利率；否则直接使用客户设置的月供倍率
        if self.is_private:
            rate = Decimal('0.003')
            self.cost = (self.amount or 0) * rate * (self.days_used or 0)
        else:
            # 获取客户设置的月供倍率，如果未设置则使用默认值0.002
            multiplier = getattr(self.customer, 'monthly_payment_multiplier', None) or Decimal('0.002')
            self.cost = (self.amount or 0) * multiplier * (self.days_used or 0)
        return self.cost

    class Meta:
        verbose_name = "月供出款记录"
        verbose_name_plural = "月供出款记录"

class CreditCardPayment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="客户")
    bank = models.CharField("银行", max_length=50)
    payment_date = models.DateField("出款时间",null=True,blank=True)
    payment_amount = models.DecimalField("出款金额", max_digits=12, decimal_places=2, default=0, null=True,blank=True)
    withdrawal_amount = models.DecimalField("刷出金额", max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    withdrawal_date = models.DateField("刷出时间", null=True, blank=True)
    notes = models.CharField("备注", max_length=200, blank=True)
    fee = models.DecimalField("信用卡费率", max_digits=12, decimal_places=2, default=0, null=True, blank=True)

    def calculate_fee(self):
        from decimal import Decimal
        # 获取客户设置的信用卡倍率，如果未设置则使用默认值0.03
        multiplier = getattr(self.customer, 'credit_card_multiplier', None) or Decimal('0.03')
        self.fee = (self.payment_amount or 0) * multiplier
        return self.fee

    class Meta:
        verbose_name = "信用卡出款记录"
        verbose_name_plural = "信用卡出款记录"


class CustomerImage(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="客户")
    title = models.CharField("图片标题", max_length=100, blank=True)
    image = models.ImageField("图片文件", upload_to='customer_images/')
    uploaded_at = models.DateTimeField("上传时间", auto_now_add=True)

    class Meta:
        verbose_name = "客户图片"
        verbose_name_plural = "客户图片"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.customer.name} - {self.title or '未命名图片'}"


class CustomerServicePhone(models.Model):
    bank_name = models.CharField("银行/机构名称", max_length=100)
    phone_number = models.CharField("客服电话", max_length=50)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "客服电话"
        verbose_name_plural = "客服电话"
        ordering = ['bank_name']

    def __str__(self):
        return f"{self.bank_name} - {self.phone_number}"

