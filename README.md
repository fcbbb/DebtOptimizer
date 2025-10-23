# 债务优化管理系统 (DebtOptimizer)

## 项目简介
债务优化管理系统是一个帮助用户管理和优化个人或企业债务的应用程序。该系统可以跟踪月供、信用卡出款记录，并提供债务分析和优化建议。

## 功能特点
- 客户信息管理
- 月供出款记录跟踪
- 信用卡出款记录管理
- 债务分析与优化
- 数据导入/导出功能
- 直观的用户界面

## 系统要求
- Python 3.8 或更高版本
- 所需依赖包见 requirements.txt

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

## 项目结构
```
DebtOptimizer/
├── DebtOptimizer/       # 项目配置目录
├── core/                # 核心应用
│   ├── models.py        # 数据模型
│   ├── views.py         # 视图函数
│   ├── urls.py          # URL配置
│   ├── utils/           # 工具函数
│   └── migrations/      # 数据库迁移文件
├── templates/           # HTML模板
├── static/              # 静态文件
├── db.sqlite3           # SQLite数据库
├── manage.py            # Django管理脚本
├── run.py               # 自定义启动脚本
├── run.bat              # 一键启动批处理文件
├── requirements.txt     # 依赖包列表
└── README.md            # 项目说明文档
```

## 数据导入/导出
1. 登录系统后，进入"导入数据"页面
2. 选择Excel文件并上传
3. 系统会自动解析并导入数据
4. 导出功能可在客户详情页使用

## 注意事项
1. 首次运行时，系统会自动创建数据库和超级用户
2. 默认用户名和密码：admin/admin
3. 请在生产环境中修改默认密码和SECRET_KEY
4. 定期备份数据库文件 (db.sqlite3)

## 联系方式
如有任何问题或建议，请联系开发人员。