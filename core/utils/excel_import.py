# core/utils/excel_import.py
import pandas as pd
from datetime import datetime
from core.models import Customer, CreditCard, Loan, MonthlyPayment, CreditCardPayment


def safe_decimal(val):
    """
    安全地将值转换为可用于 DecimalField 的值。
    如果是 NaN 或无效，则返回 None。
    """
    if pd.isna(val):
        return None  # 这是关键！返回 None，而不是 0
    try:
        # 尝试转换为 float
        return float(val)
    except (ValueError, TypeError):
        return None

def parse_excel_date(val):
    """将Excel单元格值安全解析为 datetime.date 对象，支持数字日期、中文日期、斜杠和连字符分隔日期格式"""
    if pd.isna(val):
        return None
    if isinstance(val, datetime):
        return val.date()
    # --- 新增：处理 Excel 数字序列号（如 45841 表示 2025/7/12）---
    if isinstance(val, (int, float)):
        try:
            # Excel 日期是从 1900-01-01 开始的天数（注意：Excel 有 1900 闰年 bug）
            # 使用 pandas 的 Excel 兼容模式
            dt = pd.to_datetime(val - 2, unit='D', origin='1900-01-01')  # 减2是因为 Excel 错把 1900 当闰年
            return dt.date()
        except:
            pass  # 如果失败，继续后续解析
    try:
        # 尝试直接解析
        return pd.to_datetime(val).date()
    except:
        # 尝试处理各种日期格式
        if isinstance(val, str):
            import re
            # 匹配中文日期格式，如"7月4日"或"2025年7月4日"
            match = re.search(r'(\d{4}年)?(\d+)月(\d+)日', val.strip())
            if match:
                year = match.group(1)
                month = int(match.group(2))
                day = int(match.group(3))
                # 如果没有年份，使用当前年份
                if not year:
                    year = datetime.now().year
                else:
                    year = int(year[:-1])  # 去掉"年"字
                try:
                    return datetime(year, month, day).date()
                except ValueError:
                    return None
            
            # 匹配斜杠分隔日期格式，如"2025/6/23"或"6/23"
            match = re.search(r'(\d{4}/)?(\d+)/(\d+)', val.strip())
            if match:
                year = match.group(1)
                month = int(match.group(2))
                day = int(match.group(3))
                # 如果没有年份，使用当前年份
                if not year:
                    year = datetime.now().year
                else:
                    year = int(year[:-1])  # 去掉"/"字
                try:
                    return datetime(year, month, day).date()
                except ValueError:
                    return None
            
            # 匹配连字符分隔日期格式，如"2025-06-23"或"6-23"
            match = re.search(r'(\d{4}-)?(\d+)-(\d+)', val.strip())
            if match:
                year = match.group(1)
                month = int(match.group(2))
                day = int(match.group(3))
                # 如果没有年份，使用当前年份
                if not year:
                    year = datetime.now().year
                else:
                    year = int(year[:-1])  # 去掉"-"字
                try:
                    return datetime(year, month, day).date()
                except ValueError:
                    return None
        return None

def extract_day_only(val):
    """从单元格值中提取日号（1-31）"""
    if pd.isna(val):
        return None
    try:
        if isinstance(val, (int, float)):
            day = int(val)
            return day if 1 <= day <= 31 else None
        elif isinstance(val, str):
            import re
            numbers = re.findall(r'\d+', val)
            if numbers:
                day = int(numbers[0])
                return day if 1 <= day <= 31 else None
    except:
        return None
    return None

def find_keyword_position(df, keyword):
    """在DataFrame中搜索关键词，返回(行, 列)"""
    for (row_idx, col_idx), value in df.stack().items():
        if isinstance(value, str) and keyword in value:
            return (row_idx, col_idx)
    return None

def is_sheet_empty(df, sample_rows=5, sample_cols=5):
    """
    检查一个DataFrame（工作表）是否为空。
    检查前几行和前几列的交集区域是否全为空。
    """
    # 取前 sample_rows 行和前 sample_cols 列
    sample_df = df.iloc[:sample_rows, :sample_cols]
    # 如果这个区域的所有值都是 NaN 或空，则认为工作表为空
    return sample_df.isna().all().all() or sample_df.astype(str).eq('').all().all()

def import_customer_from_excel(file, company):
    """
    从Excel模板导入客户数据（支持多Sheet，自动跳过空Sheet）
    使用指定的公司，不从Excel中查找公司信息
    """
    imported_customers = []  # 记录成功导入的客户
    errors = []              # 记录错误信息

    try:
        # 使用 pd.ExcelFile 可以访问所有工作表
        excel_file = pd.ExcelFile(file)

        for sheet_name in excel_file.sheet_names:
            # 读取当前工作表
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
            
            # --- 检查工作表是否为空 ---
            if is_sheet_empty(df):
                break  # 遇到空工作表，停止

            # --- 在当前工作表中查找客户信息 ---
            name_label_pos = find_keyword_position(df, "客户姓名")
            if not name_label_pos:
                # 如果这个工作表没有客户信息，跳过
                continue

            # --- 1. 提取基本信息 ---
            # 姓名在 "客户姓名" 标题的正下方两个
            name_row = name_label_pos[0] + 2
            name_col = name_label_pos[1]
            name = df.iloc[name_row, name_col]
            name = str(name).strip() if not pd.isna(name) else "未知客户"

            # 电话在 "电话及微信号" 标题的正下方
            phone = ""
            phone_label_pos = find_keyword_position(df, "电话及微信号")
            if phone_label_pos:
                phone_row = phone_label_pos[0] + 1
                phone_col = phone_label_pos[1]
                phone = df.iloc[phone_row, phone_col]
                phone = str(phone).strip() if not pd.isna(phone) else ""

            # 创建或获取客户
            customer, created = Customer.objects.get_or_create(
                name=name,
                defaults={"phone": phone, "company": company}
            )
            # 更新公司信息（如果客户已存在）
            if not created and customer.company != company:
                customer.company = company
                customer.save()
            # 清除旧数据
            CreditCard.objects.filter(customer=customer).delete()
            Loan.objects.filter(customer=customer).delete()
            MonthlyPayment.objects.filter(customer=customer).delete()
            CreditCardPayment.objects.filter(customer=customer).delete()

            # --- 2. 导入信用卡账单明细 ---
            cc_section_pos = find_keyword_position(df, "信用卡账单明细")
            if cc_section_pos:
                header_row = cc_section_pos[0] + 1
                data_row = header_row + 1
                col_mapping = {}
                for col in range(df.shape[1]):
                    header_val = df.iloc[header_row, col]
                    if pd.notna(header_val):
                        header_str = str(header_val)
                        if "银行渠道" in header_str:
                            col_mapping['bank'] = col
                        elif "总授信额度" in header_str:
                            col_mapping['total_limit'] = col
                        elif "有无分期" in header_str:
                            col_mapping['has_installment'] = col
                        elif "分期金额" in header_str:
                            col_mapping['installment_amount'] = col
                        elif "账单日" in header_str:
                            col_mapping['billing_date'] = col
                        elif "还款日" in header_str:
                            col_mapping['repayment_date'] = col

                row = data_row
                while row < df.shape[0]:
                    bank_val = df.iloc[row, col_mapping.get('bank', -1)]
                    if pd.isna(bank_val) or str(bank_val).strip() == '':
                        break
                    try:
                        CreditCard.objects.create(
                            customer=customer,
                            bank=str(bank_val),
                            total_limit=safe_decimal(df.iloc[row, col_mapping.get('total_limit', -1)]),           # 修正
                            has_installment=bool(df.iloc[row, col_mapping.get('has_installment', -1)]),           # 这个字段是布尔值，不需要 safe_decimal
                            installment_amount=safe_decimal(df.iloc[row, col_mapping.get('installment_amount', -1)]), # 修正
                            # total_limit=df.iloc[row, col_mapping.get('total_limit', -1)] or 0,
                            # has_installment=bool(df.iloc[row, col_mapping.get('has_installment', -1)]),
                            # installment_amount=df.iloc[row, col_mapping.get('installment_amount', -1)] or 0,
                            billing_date=extract_day_only(df.iloc[row, col_mapping.get('billing_date', -1)]),
                            repayment_date=extract_day_only(df.iloc[row, col_mapping.get('repayment_date', -1)]),
                        )
                    except Exception as e:
                        pass  # 静默处理错误
                    row += 1

            # --- 3. 导入信用贷款 ---
            loan_section_pos = find_keyword_position(df, "信用贷款账单明细")
            if loan_section_pos:
                header_row = loan_section_pos[0] + 1
                data_row = header_row + 1
                col_mapping = {}
                for col in range(df.shape[1]):
                    header_val = df.iloc[header_row, col]
                    if pd.notna(header_val):
                        header_str = str(header_val)
                        if "银行渠道" in header_str:
                            col_mapping['bank'] = col
                        elif "总授信额度" in header_str:
                            col_mapping['total_limit'] = col
                        elif "贷款余额" in header_str:
                            col_mapping['balance'] = col
                        elif "月还款" in header_str:
                            col_mapping['monthly_payment'] = col
                        elif "到期时间" in header_str:
                            col_mapping['due_date'] = col
                        elif "还款日" in header_str:
                            col_mapping['repayment_date'] = col

                row = data_row
                while row < df.shape[0]:
                    bank_val = df.iloc[row, col_mapping.get('bank', -1)]
                    if pd.isna(bank_val) or str(bank_val).strip() == '':
                        break
                    try:
                        Loan.objects.create(
                            customer=customer,
                            bank=str(bank_val),
                            total_limit=safe_decimal(df.iloc[row, col_mapping.get('total_limit', -1)]),           # 修正
                            balance=safe_decimal(df.iloc[row, col_mapping.get('balance', -1)]),                   # 修正
                            monthly_payment=safe_decimal(df.iloc[row, col_mapping.get('monthly_payment', -1)]),   # 修正
                            # total_limit=df.iloc[row, col_mapping.get('total_limit', -1)] or 0,
                            # balance=df.iloc[row, col_mapping.get('balance', -1)] or 0,
                            # monthly_payment=df.iloc[row, col_mapping.get('monthly_payment', -1)] or 0,
                            due_date=parse_excel_date((df.iloc[row, col_mapping.get('due_date', -1)])),
                            repayment_date=extract_day_only(df.iloc[row, col_mapping.get('repayment_date', -1)]),
                        )
                    except Exception as e:
                        pass  # 静默处理错误
                    row += 1

            # --- 4. 导入月供出款记录 ---
            mp_section_pos = find_keyword_position(df, "月供出款明细")
            if mp_section_pos:
                header_row = mp_section_pos[0] + 1
                data_row = header_row + 1
                col_mapping = {}
                for col in range(mp_section_pos[1], mp_section_pos[1]+3):

                    header_val = df.iloc[header_row, col]
                    if pd.notna(header_val):
                        header_str = str(header_val)
                        if "出款时间" in header_str:
                            col_mapping['payment_date'] = col
                        elif "出款金额" in header_str:
                            col_mapping['amount'] = col
                        elif "备注" in header_str:
                            col_mapping['notes'] = col

                row = data_row
                while row < df.shape[0]:
                    # 获取日期值并解析
                    date_val = df.iloc[row, col_mapping.get('payment_date', -1)]
                    if pd.isna(date_val):
                        break
                     
                    # 解析日期（支持中文日期格式）
                    parsed_date = parse_excel_date(date_val)
                    if parsed_date is None:
                        row += 1
                        continue
                     
                    # 读取备注单元格的值并安全转换为字符串
                    notes_val = df.iloc[row, col_mapping.get('notes', -1)]
                    notes = ""
                    if not pd.isna(notes_val):
                        try:
                            notes = str(notes_val).strip()  # 转为字符串并去除首尾空格
                        except:
                            notes = ""
                     
                    try:
                        MonthlyPayment.objects.create(
                            customer=customer,
                            payment_date=parsed_date,
                            amount=safe_decimal(df.iloc[row, col_mapping.get('amount', -1)]),
                            notes=notes
                        )
                    except Exception as e:
                        pass  # 静默处理错误
                    row += 1

            # --- 5. 导入信用卡出款记录 ---
            ccp_section_pos = find_keyword_position(df, "信用卡出款明细")
            if ccp_section_pos:
                header_row = ccp_section_pos[0] + 1
                data_row = header_row + 1
                col_mapping = {}
                for col in range(ccp_section_pos[1], ccp_section_pos[1]+5):


                    header_val = df.iloc[header_row, col]
                    if pd.notna(header_val):
                        header_str = str(header_val)
                        if "出款时间" in header_str:
                            col_mapping['payment_date'] = col
                        elif "银行" in header_str:
                            col_mapping['bank'] = col
                        elif "出款金额" in header_str:
                            col_mapping['payment_amount'] = col
                        elif "刷出金额" in header_str:
                            col_mapping['withdrawal_amount'] = col
                        elif "刷出时间" in header_str:
                            col_mapping['withdrawal_date'] = col

                row = data_row
                while row < df.shape[0]:
                    bank_val = df.iloc[row, col_mapping.get('bank', -1)]
                    if pd.isna(bank_val):
                        break
                    try:
                        CreditCardPayment.objects.create(
                            customer=customer,
                            bank=str(bank_val),
                            payment_date=parse_excel_date(df.iloc[row, col_mapping.get('payment_date', -1)]),
                            payment_amount=safe_decimal(df.iloc[row, col_mapping.get('payment_amount', -1)]),
                            withdrawal_amount=safe_decimal(df.iloc[row, col_mapping.get('withdrawal_amount', -1)]),
                            withdrawal_date=parse_excel_date(df.iloc[row, col_mapping.get('withdrawal_date', -1)])
                        )
                    except Exception as e:
                        pass  # 静默处理错误
                    row += 1

            # 记录成功导入的客户
            imported_customers.append(customer)

        # 返回结果
        if imported_customers:
            # 返回最后一个导入的客户对象
            return imported_customers[-1], None
        else:
            return None, "未在任何工作表中找到有效的客户信息。"

    except Exception as e:
        return None, f"文件解析失败：{str(e)}"