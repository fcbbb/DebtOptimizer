# -*- mode: python ; coding: utf-8 -*-

import django
import os
import sys
from pathlib import Path

# 获取当前工作目录作为项目目录
project_dir = os.getcwd()
sys.path.append(project_dir)

# 获取Django路径
django_path = django.__path__[0]
print(f"Django路径: {django_path}")

block_cipher = None

# 收集静态文件
def get_static_files():
    static_files = []
    
    # 收集项目静态文件
    static_dirs = [
       # ('static', 'static'),
       # ('templates', 'templates'),
    ]
    # !!! 必须添加项目配置文件 !!!
    static_files.extend([
        ('manage.py', '.'),                  # 项目根目录文件
        ('DebtOptimizer/settings.py', 'DebtOptimizer'), # Django设置文件
        ('DebtOptimizer/settings_desktop.py', 'DebtOptimizer'), # 桌面应用设置文件
        ('DebtOptimizer/urls.py', 'DebtOptimizer'),
        ('DebtOptimizer/wsgi.py', 'DebtOptimizer'),
        ('DebtOptimizer/asgi.py', 'DebtOptimizer'),  # ASGI应用文件
        ('DebtOptimizer/celery.py', 'DebtOptimizer'),  # Celery配置文件
        ('DebtOptimizer/__init__.py', 'DebtOptimizer'), # 确保 __init__.py 被添加
        ('loading.html', '.'),  # 加载页面
        ('.env', '.'),  # 环境变量文件  
    ])
    
    
    for target, source in static_dirs:
        source_path = os.path.join(project_dir, source)
        if os.path.exists(source_path):
            for root, dirs, files in os.walk(source_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.join(target, os.path.relpath(file_path, source_path)).replace('\\', '/')
                    static_files.append((file_path, arc_path))
    
    # 收集Django管理静态文件（如果存在）
    django_admin_static = os.path.join(django_path, 'contrib', 'admin', 'static')
    if os.path.exists(django_admin_static):
        for root, dirs, files in os.walk(django_admin_static):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.join('static/admin', os.path.relpath(file_path, django_admin_static)).replace('\\', '/')
                static_files.append((file_path, arc_path))


    # 仅添加缺失的 C 源代码文件
    site_packages_path = Path(r"C:\Users\FCB\AppData\Roaming\Python\Python312\site-packages")
    autobahn_nvx_path = site_packages_path / "autobahn" / "nvx"

    # 目标目录是 'autobahn/nvx'，这是应用程序在运行时查找的位置
    target_dir = 'autobahn/nvx'

    if autobahn_nvx_path.exists():
        # 仅添加 .c 文件
        c_files_to_add = [
            '_utf8validator.c',
            '_xormasker.c',
        ]
        
        for file_name in c_files_to_add:
            file_path = autobahn_nvx_path / file_name
            if file_path.is_file():
                static_files.append((str(file_path), target_dir))

    # ... (保持项目静态文件和Django Admin静态文件的添加不变)
    
    
    return static_files

PIL_BASE_DIR = 'f:\\python\\lib\\site-packages\\PIL'

a = Analysis(
    ['run_server.py'],
    pathex=[project_dir],
    binaries=[],
    datas=get_static_files(),
    hiddenimports=[
        # Django核心模块
        'django',
        'django.conf',
        'django.core.management',
        'django.core.wsgi',
        'django.core.asgi',
        'django.db',
        'django.forms',
        'django.http',
        'django.shortcuts',
        'django.template',
        'django.urls',
        'django.utils',
        'django.views',
        
        # Django contrib模块
        'django.contrib.admin',
        'django.contrib.admin.apps',
        'django.contrib.admin.templatetags',
        'django.contrib.auth',
        'django.contrib.auth.apps',
        'django.contrib.contenttypes',
        'django.contrib.contenttypes.apps',
        'django.contrib.sessions',
        'django.contrib.sessions.apps',
        'django.contrib.messages',
        'django.contrib.messages.apps',
        'django.contrib.staticfiles',
        'django.contrib.staticfiles.apps',
        
        # Django管理命令
        'django.core.management.commands.migrate',
        'django.core.management.commands.collectstatic',
        
        # Channels和Daphne相关模块
        'channels',
        'daphne',
        'channels.layers',
        'channels.routing',
        'channels.generic',
        'channels.generic.websocket',
        'channels.db',
        'channels.auth',
        
        # 项目模块
        'core',
        'core.apps',
        'core.context_processors',
        'core.templatetags',
        'core.templatetags.custom_filters',
        'core.apps.CoreConfig',
        
        'ai_agent',
        'ai_agent.apps',
        'ai_agent.apps.AiAgentConfig',
        'ai_agent.models',
        'ai_agent.views',
        'ai_agent.urls',
        'ai_agent.consumers',
        'ai_agent.chat_consumers',
        'ai_agent.ocr_consumer',
        'ai_agent.routing',
        'ai_agent.serializers',
        'ai_agent.tasks',
        'ai_agent.temp_storage',
        'ai_agent.llm_use',
        'ai_agent.llm_use.llm_agent',
        'ai_agent.llm_use.llm_chat',
        'ai_agent.llm_use.llm_database',
        'ai_agent.llm_use.llm_ocr',
        'ai_agent.llm_use.openai_chat',
        
        # 修复的导入
        'django.templatetags.static',  # 替代已废弃的admin_static
        'django.contrib.admin.apps.AdminConfig',  # 替代SimpleAdminConfig
        
        # 添加webview和pythonnet相关模块
        'webview',
        'webview.platforms.winforms',
        'clr',
        'pythonnet',
        'cffi',
        'pycparser',
        'clr_loader',
        'pyi_splash',

        # 数据处理相关模块
        'numpy', 
        'pytz', 
        'pandas', 
        'pandas.core.arrays.numpy_', # 增加 Pandas 核心依赖
        'pandas._libs.tslibs',       # 解决可能的子模块导入问题
        'openpyxl',
        'xlrd',
        
        # 图像处理相关模块
        'PIL', 
        'PIL._imaging', 
        'PIL.Image',
        'PIL.ImageOps',
        'PIL.ImageEnhance',
        'PIL.ImageFilter',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        
        # AI相关模块
        'dashscope',
        'langchain',
        'langchain_core',
        'langchain_community',
        'langchain_openai',
        'aiohttp',
        'asyncio',
        
        # 其他必要模块
        'dotenv',
        'celery',
        'celery.fixups',
        'celery.loaders.app',
        'celery.fixups.django',
        'autobahn',
        'autobahn.nvx',
        'autobahn.nvx._utf8validator',
        'autobahn.nvx._xormasker',
        # 推荐添加 Twisted 的相关导入，以防丢失
        'twisted', 
        'twisted.web',
        'twisted.internet',
        'twisted.internet.reactor',
        # 确保与加密相关的库被 PyInstaller 找到 (如果仍报错)
        'cryptography.hazmat.bindings._openssl', 
        'cryptography.hazmat.bindings._rust',    # 新版本可能需要
        'sqlalchemy.ext.declarative',
        'sqlalchemy.orm',
        'sqlalchemy.dialects',


        'redis',
        'tkinter',
        'socket',
        'gc',
        'threading',
        'time',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不必要的大型模块
        'scipy',
        'matplotlib',
        'tensorflow',
        'torch',
        'sklearn',
        'IPython',
        'jupyter',
        'notebook',
        # 注意：我们不完全排除sqlite3，因为Django需要它
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

splash = Splash(
    "splash.png",
    binaries=a.binaries,
    datas=a.datas,
    excludes=a.excludes,
)

# 内存优化的PYZ配置
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 内存优化的EXE配置
exe = EXE(
    splash,  # 启动画面
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DebtOptimizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    # 测试阶段改为true
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/favicon.ico'
)