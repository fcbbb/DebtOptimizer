import unittest
from datetime import date, timedelta
from core.models import MonthlyPayment

class TestLastCustomerError(unittest.TestCase):
    def test_future_payment_date(self):
        """测试未来付款日期对days_used的影响"""
        # 创建一个月供记录，付款日期设为未来
        mp = MonthlyPayment()
        mp.payment_date = date.today() + timedelta(days=10)
        mp.amount = 1000

        # 计算资金使用成本
        mp.calculate_cost()

        # 验证days_used是否被正确处理
        self.assertGreaterEqual(mp.days_used, 0, "days_used不能为负数")

if __name__ == '__main__':
    unittest.main()