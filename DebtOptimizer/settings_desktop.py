"""
Django settings for DebtOptimizer desktop application.
"""
import os
from pathlib import Path
from .settings import *

# 强制覆盖 BASE_DIR，使用当前工作目录。
# 因为启动脚本确保在加载设置时 os.getcwd() 已经指向 EXE 所在的文件夹。
BASE_DIR = Path(os.getcwd()) 

TEMPLATES = [
    {
        # --- 核心修正：添加 BACKEND ---
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        
        # --- 您的自定义路径 ---
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True,
        
        # --- 确保包含 context_processors（通常是必需的） ---
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.company_context',  # 添加公司上下文处理器
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 为桌面应用调整设置
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0']
# ... 其他配置保持不变

# 桌面应用不需要CSRF保护（因为是本地应用）
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',  # 桌面应用中禁用CSRF
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 静态文件设置
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# 媒体文件设置
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session设置
SESSION_COOKIE_AGE = 86400  # 24小时
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

# 日志设置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'desktop_app.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
}