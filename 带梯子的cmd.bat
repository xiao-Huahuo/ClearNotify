@echo off
:: 设置你的梯子端口
set PROXY_PORT=11719

:: 注入环境变量
set http_proxy=http://127.0.0.1:%PROXY_PORT%
set https_proxy=http://127.0.0.1:%PROXY_PORT%

:: 提示信息
echo ==========================================
echo   Proxy has been in usage (Port: %PROXY_PORT%)
echo   You can run "curl -I https://www.google.com" as a test.
echo ==========================================

:: 保持窗口开启并进入交互模式
cmd /k