# 债务优化管理系统 (DebtOptimizer)

## 项目简介
债务优化管理系统是一个帮助用户管理和优化个人或企业债务的应用程序。该系统可以跟踪月供、信用卡出款记录，并提供债务分析和优化建议。系统采用Django框架开发，具有现代化的用户界面和丰富的功能特性。

## 功能特点
- 客户信息管理：完整的客户资料管理，包括基本信息、合同日期、融资日期等
- 月供出款记录跟踪：详细记录每月还款信息
- 信用卡出款记录管理：管理信用卡消费和还款记录
- 公司管理：支持多公司数据管理
- 还款日历：直观的还款时间视图
- 客服电话管理：维护客服联系信息
- 债务分析与优化：提供债务分析和优化建议
- 数据导入/导出功能：支持Excel格式的数据导入导出
- AI助手集成：集成AI聊天助手提供智能服务
- 直观的用户界面：现代化响应式设计，支持多设备访问

## 系统要求
- Python 3.8 或更高版本
- Windows/Linux/macOS 操作系统
- 所需依赖包见 requirements.txt

## 技术栈
- 后端框架：Django 4.2+
- 前端框架：Bootstrap 5
- 数据库：SQLite（默认），支持PostgreSQL、MySQL等
- 异步处理：Celery + Redis
- 实时通信：Django Channels
- AI集成：LangChain + DashScope
- 数据处理：Pandas + OpenPyXL

## 快速启动
### 方法1：使用一键启动脚本（推荐）
1. 确保已安装 Python 3.8 或更高版本
2. 双击运行 `run.bat` 文件
3. 系统会自动安装依赖、创建数据库并启动服务器
4. 浏览器会自动打开，访问 http://127.0.0.1:8000

### 方法2：手动启动
1. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```
2. 数据库迁移：
   ```bash
   python manage.py migrate
   ```
3. 启动服务器：
   ```bash
   python manage.py runserver 8000
   ```
4. 在浏览器中访问 http://127.0.0.1:8000

### 方法3：桌面应用模式
系统还支持打包为桌面应用程序：
1. 使用PyInstaller打包：
   ```bash
   pyinstaller test.spec
   ```
2. 运行生成的可执行文件

## 项目结构
```
DebtOptimizer/
├── DebtOptimizer/           # 项目配置目录
│   ├── settings.py          # 主要配置文件
│   ├── settings_desktop.py  # 桌面应用配置
│   ├── urls.py             # 主URL配置
│   └── wsgi.py             # WSGI配置
├── core/                    # 核心应用
│   ├── models.py            # 数据模型（客户、月供、信用卡等）
│   ├── views.py             # 视图函数
│   ├── urls.py              # URL配置
│   ├── forms.py             # 表单定义
│   ├── admin.py             # 后台管理配置
│   ├── utils/               # 工具函数（Excel导入导出等）
│   ├── templatetags/        # 自定义模板标签
│   └── migrations/          # 数据库迁移文件
├── ai_agent/                # AI代理应用
│   ├── models.py            # AI相关数据模型
│   ├── views.py             # AI视图函数
│   ├── consumers.py         # WebSocket消费者
│   ├── llm_use/             # 大语言模型集成
│   └── migrations/          # 数据库迁移文件
├── templates/               # HTML模板
├── static/                  # 静态文件
│   ├── css/                 # 样式文件
│   ├── js/                  # JavaScript文件
│   ├── img/                 # 图片资源
│   └── icons/               # 图标文件
├── media/                   # 用户上传文件
├── build/                   # PyInstaller构建文件（临时）
├── dist/                    # PyInstaller输出文件（可执行程序）
├── db.sqlite3               # SQLite数据库
├── manage.py                # Django管理脚本
├── run.py                   # 自定义启动脚本
├── run.bat                  # 一键启动批处理文件
├── test.spec                # PyInstaller打包配置
├── requirements.txt         # 依赖包列表
└── README.md                # 项目说明文档
```

## 核心功能模块
### 客户管理
- 客户信息录入和编辑
- 客户档案详情查看
- 客户数据导入导出
- 客户归档管理

### 债务跟踪
- 月供记录管理
- 信用卡消费记录
- 还款提醒功能
- 债务统计分析

### 公司管理
- 多公司数据隔离
- 公司信息维护
- 按公司筛选数据

### 还款日历
- 可视化还款时间轴
- 临近还款提醒
- 还款状态跟踪

### AI助手
- 智能客服对话
- 债务咨询建议
- 数据查询辅助

## 数据导入/导出
1. 登录系统后，进入"导入数据"页面
2. 选择Excel文件并上传（支持.xls和.xlsx格式）
3. 系统会自动解析并导入数据
4. 导出功能可在客户详情页使用

## 管理员功能
1. 默认管理员账户：admin/admin
2. 可通过Django后台管理所有数据
3. 用户权限管理
4. 系统配置调整

## 注意事项
1. 首次运行时，系统会自动创建数据库和超级用户
2. 默认用户名和密码：admin/admin
3. 请在生产环境中修改默认密码和SECRET_KEY
4. 定期备份数据库文件 (db.sqlite3)
5. 如需部署到生产环境，建议使用PostgreSQL等专业数据库

## 常见问题
### 启动失败
- 确保已安装Python 3.8+
- 检查依赖包是否完整安装
- 确认端口8000未被占用

### 数据导入问题
- 确保Excel文件格式正确
- 检查列名是否匹配系统要求
- 避免在导入时修改数据文件

### AI功能异常
- 检查网络连接状态
- 确认API密钥配置正确
- 查看日志文件排查错误

## 联系方式
如有任何问题或建议，请联系开发人员。