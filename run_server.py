import os
import sys
import threading
import time
import gc
import webview
import socket
import tkinter # splash需要
import pyi_splash

# 添加项目根目录到Python路径
if getattr(sys, 'frozen', False):
    # 如果是打包后的exe环境
    application_path = os.path.dirname(sys.executable)
else:
    # 开发环境
    application_path = os.path.dirname(os.path.abspath(__file__))
    
    
from dotenv import load_dotenv
dotenv_path = os.path.join(application_path, '.env')

# 调试输出（可临时保留）
print(f"Application path: {application_path}")
print(f".env path: {dotenv_path}")
print(f".env exists: {os.path.exists(dotenv_path)}")

load_dotenv(dotenv_path, override=True)  # override=True 确保覆盖已有变量

# 再次验证
print("OPENAI_API_KEY loaded:", bool(os.getenv("OPENAI_API_KEY")))

sys.path.insert(0, application_path)

# 设置Django环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DebtOptimizer.settings_desktop')

# 在Django初始化前设置环境变量
os.environ['PYTHONPATH'] = application_path



def start_django_server():
    import django
    from django.core.management import execute_from_command_line
    from django.conf import settings
    """在单独线程中启动Django服务器"""
    try:
        # 预先初始化Django
        django.setup()
        
        # 执行数据库迁移检查
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        
        # 启动服务器，优化参数
        execute_from_command_line([
            'manage.py', 
            'runserver', 
            '127.0.0.1:8000', 
            '--noreload',     # 禁用自动重载以提升性能
            '--insecure',     # 允许在DEBUG=False时提供静态文件
            '--nothreading',  # 禁用多线程以减少资源消耗
            '--verbosity', '0'  # 降低日志输出级别
        ])
    except Exception as e:
        print(f"Django服务器启动错误: {e}")

def wait_for_server_ready(host, port, timeout=30.0):
    """检查本地端口是否开放"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.1):
                return True
        except (socket.error, ConnectionRefusedError):
            time.sleep(0.1)
    return False

def background_server_loader(window):
    """
    在后台启动服务器，并在成功后加载URL。
    """
    # 启动Django服务器线程
    server_thread = threading.Thread(target=start_django_server, daemon=True)
    server_thread.start()

    # 等待服务器端口准备就绪
    if wait_for_server_ready('127.0.0.1', 8000):
        print("服务器已就绪，正在加载应用...")
        # 服务器就绪后，加载真正的URL
        window.load_url('http://127.0.0.1:8000')
    else:
        print("错误: 服务器在指定时间内未能启动。")
        # 显示错误信息
        window.load_html('<h1 style="text-align: center; margin-top: 50px;">错误</h1><p style="text-align: center;">服务器启动超时，请重启应用。</p>')

def get_loading_html():
    """获取加载页面的HTML内容"""
    return '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>正在启动...</title>
        <style>
            body {
                background-color: #f0f2f5;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                color: #333;
                overflow: hidden;
            }
            .container {
                text-align: center;
            }
            .spinner {
                border: 4px solid rgba(0, 0, 0, 0.1);
                width: 36px;
                height: 36px;
                border-radius: 50%;
                border-left-color: #09f;
                animation: spin 1s ease infinite;
                margin: 0 auto 20px;
            }
            @keyframes spin {
                0% {
                    transform: rotate(0deg);
                }
                100% {
                    transform: rotate(360deg);
                }
            }
            p {
                font-size: 16px;
                color: #555;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="spinner"></div>
            <p>正在启动债务优化管理系统，请稍候...</p>
        </div>
    </body>
    </html>
    '''

def create_window():
    pyi_splash.close()  # ←←← 这行代码会让启动图消失！
    
    """创建并返回webview窗口"""
    # 获取加载页面HTML
    loading_html = get_loading_html()
    
    # 创建窗口，显示加载页面
    window = webview.create_window(
        "债务优化器", 
        html=loading_html,  # 使用内联HTML确保能正确显示
        width=1200, 
        height=800,
        resizable=True,
        fullscreen=False,
        min_size=(800, 600)
    )
    
    return window

def main():
    # 优化垃圾回收
    gc.set_threshold(700, 10, 10)
    
    # 设置当前工作目录为应用程序目录，确保数据库文件路径正确
    os.chdir(application_path)
    
    # 立即创建窗口，显示加载页面
    window = create_window()
    
    # 立即启动后台加载任务
    loader_thread = threading.Thread(target=background_server_loader, args=(window,), daemon=True)
    loader_thread.start()
    
    # 启动窗口（禁用调试模式以提升性能）
    webview.start(debug=False, http_server=False, private_mode=False)

if __name__ == '__main__':
    main()