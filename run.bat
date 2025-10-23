@echo off
chcp 65001
echo.
echo **********************************************
echo        债务优化管理系统 (DebtOptimizer)
echo           本地运行版 - 无需联网
echo **********************************************
echo.

echo 正在启动系统...
echo 请确保已安装Python和依赖包。

python run.py

if errorlevel 1 (
    echo.
    echo 出现错误，请检查环境：
    echo 1. 确保已安装 Python 3.8 或更高版本
    echo 2. 在此目录运行: pip install -r requirements.txt
    echo 3. 检查是否缺少文件
)

echo.
echo 系统已关闭。
pause