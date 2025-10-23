import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DebtOptimizer.settings')
django.setup()

from core.models import CustomerServicePhone

# 客服电话数据
customer_service_phones = [
    {"bank_name": "工商银行", "phone_number": "95588"},
    {"bank_name": "建设银行", "phone_number": "95533"},
    {"bank_name": "光大银行", "phone_number": "95595"},
    {"bank_name": "中国银行", "phone_number": "95566"},
    {"bank_name": "民生银行", "phone_number": "95568"},
    {"bank_name": "百信银行", "phone_number": "956186"},
    {"bank_name": "京东盛际小额贷款", "phone_number": "400 098 8563"},
    {"bank_name": "中信银行", "phone_number": "400-889-5558"},
    {"bank_name": "招商银行", "phone_number": "400-820-5555"},
    {"bank_name": "邮政储蓄银行", "phone_number": "40088-95580"},
    {"bank_name": "无锡锡商银行", "phone_number": "400-8880-555"},
    {"bank_name": "宁银消金客服热线", "phone_number": "400-779-6558"},
    {"bank_name": "中邮消费金融", "phone_number": "40066-95580"},
    {"bank_name": "哈尔滨消费金融", "phone_number": "400-030-0333"},
    {"bank_name": "洋钱罐客服热线", "phone_number": "400-002-1636"},
    {"bank_name": "普融花", "phone_number": "400-045-6600"},
    {"bank_name": "重庆小米消费金融", "phone_number": "400-683-7888"},
    {"bank_name": "华夏银行", "phone_number": "95577"},
    {"bank_name": "甘肃银行", "phone_number": "400-869-6666"},
    {"bank_name": "乐信分期乐", "phone_number": "95730"},
    {"bank_name": "吉林亿联银行", "phone_number": "95396"},
    {"bank_name": "蒙商消费金融", "phone_number": "400-900-9000"},
    {"bank_name": "江苏苏商银行", "phone_number": "956101"},
    {"bank_name": "浙江稠州商业银行", "phone_number": "956166"},
    {"bank_name": "上海银行", "phone_number": "95594"},
    {"bank_name": "农业银行", "phone_number": "40066-95599"},
    {"bank_name": "交通银行信用卡", "phone_number": "400-800-9888"},
    {"bank_name": "徽商银行", "phone_number": "40088-96588"},
    {"bank_name": "兰州银行", "phone_number": "40088-96799"},
    {"bank_name": "哈尔滨银行信用卡", "phone_number": "400-669-5537"},
    {"bank_name": "成都农商行", "phone_number": "95392"},
    {"bank_name": "光大银行", "phone_number": "400-820-5555"},
    {"bank_name": "成都银行", "phone_number": "95507"},
    {"bank_name": "平安银行", "phone_number": "95511"},
    {"bank_name": "马上消费金融", "phone_number": "95090"},
    {"bank_name": "苏银凯基消费金融", "phone_number": "400-116-0088"},
    {"bank_name": "武汉众邦银行", "phone_number": "400-688-6868"},
    {"bank_name": "福建华通银行", "phone_number": "4008219666"},
    {"bank_name": "北银消费金融", "phone_number": "400-669-5526"},
    {"bank_name": "江西裕民银行", "phone_number": "400-055-5520"},
    {"bank_name": "河南中原消费金融", "phone_number": "400-111-2233"},
    {"bank_name": "陕西长银消费", "phone_number": "400-009-3666"},
    {"bank_name": "湖北消费金融", "phone_number": "400-882-5137"},
    {"bank_name": "威海蓝海银行", "phone_number": "400-063-1888"},
    {"bank_name": "福建华通银行", "phone_number": "400-8219-666"},
    {"bank_name": "重庆富民银行", "phone_number": "956118"},
    {"bank_name": "渤海银行信用卡", "phone_number": "400-888-8811"},
    {"bank_name": "兴业银行", "phone_number": "95561"},
    {"bank_name": "辽宁振兴银行", "phone_number": "400-1757-999"},
    {"bank_name": "北京中关村银行", "phone_number": "956195"},
    {"bank_name": "天津金城银行", "phone_number": "95364"},
    {"bank_name": "南银法巴消费金融", "phone_number": "400-189-5302"},
    {"bank_name": "杭银消费金融", "phone_number": "400-868-9966"},
    {"bank_name": "新网银行", "phone_number": "95394"},
    {"bank_name": "厦门国际银行", "phone_number": "956085"},
    {"bank_name": "上海银行", "phone_number": "95594"},
    {"bank_name": "广发银行", "phone_number": "95508"},
    {"bank_name": "天津银行", "phone_number": "956056"},
    {"bank_name": "五矿信托", "phone_number": "400-006-7826"},
    {"bank_name": "富邦华一银行", "phone_number": "86-21-962811"},
    {"bank_name": "海尔消费金融", "phone_number": "400-018-7777"},
    {"bank_name": "四川唯品富邦消费", "phone_number": "400-0789-333"},
    {"bank_name": "浦发银行", "phone_number": "95528"},
    {"bank_name": "北京阳光消费金融", "phone_number": "400-890-0817"},
    {"bank_name": "还呗客服热线", "phone_number": "4006816666"},
    {"bank_name": "360客服热线", "phone_number": "4006030360"},
    {"bank_name": "兴业消费金融", "phone_number": "4001095561"},
    {"bank_name": "深圳中融小贷", "phone_number": "4000859066"},
    {"bank_name": "重庆众安小贷", "phone_number": "4000086820"},
    {"bank_name": "美团三快小贷", "phone_number": "4006086500"},
    {"bank_name": "中银消费金融", "phone_number": "95137"},
    {"bank_name": "度小满", "phone_number": "95055"},
    {"bank_name": "招联消费金融", "phone_number": "95786"},
    {"bank_name": "网商银行", "phone_number": "95188"},
    {"bank_name": "蚂蚁集团", "phone_number": "95188"},
    {"bank_name": "昆仑银行", "phone_number": "95379"},
    {"bank_name": "廊坊银行", "phone_number": "400-620-0099"},
    {"bank_name": "厦门金美信", "phone_number": "400-876-9898"},
    {"bank_name": "豆豆钱", "phone_number": "400-160-1666"},
    {"bank_name": "江山金服", "phone_number": "400-999-8291"},
    {"bank_name": "桔多多", "phone_number": "400-1071-666"},
    {"bank_name": "你我贷", "phone_number": "400-675-8066"},
    {"bank_name": "尚诚消费金融", "phone_number": "400-600-1856"},
    {"bank_name": "浙商银行", "phone_number": "95527"},
    {"bank_name": "上海华瑞银行", "phone_number": "95173"},
    {"bank_name": "江苏江南农村商业", "phone_number": "0519-96005"},
    {"bank_name": "民泰银行", "phone_number": "400-889-6521"},
    {"bank_name": "小赢卡贷", "phone_number": "952592"},
    {"bank_name": "韩亚银行", "phone_number": "400-650-9226"},
    {"bank_name": "平安消费金融", "phone_number": "400-026-6666"},
    {"bank_name": "湖南三湘银行客服", "phone_number": "0731-96500"},
    {"bank_name": "上海华瑞银行客服", "phone_number": "95173"},
    {"bank_name": "河南中原消费客服", "phone_number": "400-111-2233"},
    {"bank_name": "滴滴金融", "phone_number": "400-6080-966"},
    {"bank_name": "极融", "phone_number": "4000627626"},
    {"bank_name": "拍拍贷", "phone_number": "4001507618"},
    {"bank_name": "上海爱建信托", "phone_number": "021-64396600"},
    {"bank_name": "浙江宁银", "phone_number": "400-779-6558"},
    {"bank_name": "梅州客商", "phone_number": "956115"},
    {"bank_name": "东营银行", "phone_number": "400-629-6588"},
    {"bank_name": "盛京银行", "phone_number": "95337"},
    {"bank_name": "锦程消费", "phone_number": "4001-066-166"},
    {"bank_name": "融360", "phone_number": "10100360"},
    {"bank_name": "好分期", "phone_number": "4000856608"},
    {"bank_name": "福州富奇（360）", "phone_number": "400-6030360"},
    {"bank_name": "营口银行", "phone_number": "40078-96178"},
    {"bank_name": "盛银", "phone_number": "95337"},
    {"bank_name": "张家口", "phone_number": "400-68-96368"},
    {"bank_name": "江苏银行", "phone_number": "95319"},
    {"bank_name": "宜享花", "phone_number": "400-111-2288"},
    {"bank_name": "晋商银行", "phone_number": "9510-5588"},
    {"bank_name": "内蒙古晋商消费", "phone_number": "95105520"},
    {"bank_name": "南京银行", "phone_number": "95302"},
    {"bank_name": "北京银行", "phone_number": "95526"},
    {"bank_name": "中信消费", "phone_number": "400-01-95558"},
    {"bank_name": "四川天府银行", "phone_number": "400-16-96869"},
    {"bank_name": "财付通", "phone_number": "95017"},
    {"bank_name": "中信百信", "phone_number": "956186"}
]

def add_customer_service_phones():
    """添加客服电话数据"""
    for phone_data in customer_service_phones:
        # 检查是否已存在相同的银行名称
        if not CustomerServicePhone.objects.filter(bank_name=phone_data['bank_name']).exists():
            CustomerServicePhone.objects.create(
                bank_name=phone_data['bank_name'],
                phone_number=phone_data['phone_number']
            )
            print(f"已添加: {phone_data['bank_name']} - {phone_data['phone_number']}")
        else:
            print(f"已存在: {phone_data['bank_name']} - {phone_data['phone_number']}")

if __name__ == '__main__':
    add_customer_service_phones()
    print("所有客服电话数据已添加完成！")