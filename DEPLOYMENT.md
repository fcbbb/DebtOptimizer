# Django DebtOptimizer 项目部署指南

## 1. 环境准备

### 1.1 安装必要的系统依赖
```bash
# Ubuntu/Debian系统
apt update && apt install -y python3 python3-pip python3-venv nginx

# CentOS/RHEL系统
yum install -y python3 python3-pip python3-venv nginx
```

### 1.2 创建项目目录和虚拟环境
```bash
# 创建项目目录
mkdir -p /var/www/debtoptimizer
cd /var/www/debtoptimizer

# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate
```

## 2. 部署项目代码

### 2.1 克隆或上传项目代码
```bash
# 假设使用Git克隆代码
git clone <your-repository-url> .

# 或者上传代码到该目录
```

### 2.2 安装Python依赖
首先，更新requirements.txt文件，添加Django依赖：
```bash
# 编辑requirements.txt文件，添加以下内容
echo "django>=4.2.0" >> requirements.txt
```

然后安装所有依赖：
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. 配置生产环境

### 3.1 修改settings.py文件
```bash
nano DebtOptimizer/settings.py
```

修改以下配置：
```python
# 设置DEBUG为False
DEBUG = False

# 添加允许的主机
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com', 'server-ip-address']

# 生成一个新的SECRET_KEY
SECRET_KEY = 'your-production-secret-key'

# 可选：配置数据库为PostgreSQL或MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'debtoptimizer',
        'USER': 'dbuser',
        'PASSWORD': 'dbpassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 3.2 收集静态文件
```bash
python manage.py collectstatic
```

### 3.3 数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3.4 创建超级用户
```bash
python manage.py createsuperuser
```

## 4. 配置Gunicorn

### 4.1 安装Gunicorn
```bash
pip install gunicorn
```

### 4.2 创建Gunicorn服务文件
```bash
nano /etc/systemd/system/gunicorn_debtoptimizer.service
```

添加以下内容：
```ini
[Unit]
Description=Gunicorn daemon for DebtOptimizer
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/debtoptimizer
ExecStart=/var/www/debtoptimizer/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/debtoptimizer/debtoptimizer.sock DebtOptimizer.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 4.3 启动Gunicorn服务
```bash
systemctl start gunicorn_debtoptimizer
systemctl enable gunicorn_debtoptimizer
systemctl status gunicorn_debtoptimizer
```

## 5. 配置Nginx

### 5.1 创建Nginx配置文件
```bash
nano /etc/nginx/sites-available/debtoptimizer
```

添加以下内容：
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com server-ip-address;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /var/www/debtoptimizer;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/debtoptimizer/debtoptimizer.sock;
    }
}
```

### 5.2 启用Nginx配置
```bash
ln -s /etc/nginx/sites-available/debtoptimizer /etc/nginx/sites-enabled/
nginx -t  # 测试配置是否正确
systemctl restart nginx
systemctl enable nginx
```

## 6. 配置防火墙
```bash
# 允许HTTP和HTTPS流量
ufw allow 'Nginx Full'
```

## 7. 部署SSL证书（可选但推荐）
使用Certbot获取免费的SSL证书：
```bash
# 安装Certbot
apt install certbot python3-certbot-nginx

# 获取并配置SSL证书
certbot --nginx -d your-domain.com -d www.your-domain.com
```

## 8. 定期备份（推荐）
设置定时任务备份数据库和重要文件：
```bash
# 编辑定时任务
crontab -e

# 添加以下行（每天凌晨2点备份数据库）
0 2 * * * /var/www/debtoptimizer/venv/bin/python /var/www/debtoptimizer/manage.py dumpdata > /var/backups/debtoptimizer_$(date +\%Y\%m\%d).json
```

## 9. 部署完成
现在您可以通过浏览器访问 http://your-domain.com 或 https://your-domain.com（如果配置了SSL）来访问您的应用。