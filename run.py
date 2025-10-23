# run.py
import os
import sys
import webbrowser
import threading
import time
import subprocess

def open_browser():
    """延迟打开浏览器"""
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8000")

def main():
    # 设置Django环境
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DebtOptimizer.settings')

    # 添加项目根目录到路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable?"
        ) from exc

    # 如果是第一次运行，执行migrate
    if not os.path.exists('db.sqlite3'):
        result = subprocess.run([sys.executable, 'manage.py', 'migrate'], capture_output=True, text=True)
        if result.returncode != 0:
            return

    # 启动服务器

    # 检查是否是主进程（非服务器重启）
    if os.environ.get('RUN_MAIN') != 'true':
        # 在新线程中打开浏览器
        threading.Thread(target=open_browser, daemon=True).start()

    # 运行Django开发服务器
    execute_from_command_line(['manage.py', 'runserver', '8000'])

if __name__ == '__main__':
    main()